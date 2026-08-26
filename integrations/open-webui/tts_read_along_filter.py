"""
title: TTS Read-Along & Paragraph Optimizer
author: Markus
description: Optimizes assistant responses for natural, low-latency TTS. Strips emojis, converts keycaps, preserves digits/numbers exactly, groups bullet lists in single paragraphs, expands currencies/symbols, and ensures natural speech prosody.
version: 1.6.0
license: MIT
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable
import aiohttp
import json
import re


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=10,
            description="Priority of this filter in the Open WebUI pipeline."
        )
        use_task_model: bool = Field(
            default=True,
            description="Use fast LLM task model for paragraph restructuring (with deterministic fallback)."
        )
        task_model: str = Field(
            default="gemma3:4b",
            description="Task model name (e.g. gemma3:4b, llama3.2:3b)."
        )
        task_api_url: str = Field(
            default="http://localhost:11434/v1",
            description="URL of the OpenAI/Ollama API endpoint (must be explicitly configured in Valves)."
        )
        task_api_key: str = Field(
            default="ollama",
            description="API key if required."
        )
        clean_markdown: bool = Field(
            default=True,
            description="Strips visual Markdown formatting (**, __, code blocks, horizontal rules) for clean speech."
        )
        debug: bool = Field(
            default=True,
            description="Enable verbose debug logs in Open WebUI server output."
        )
        custom_system_prompt: str = Field(
            default=(
                "Du bist ein Text-Strukturierer für Sprachsynthese (TTS) mit 1:1-Mitlesbarkeit am Bildschirm.\n\n"
                "AUFGABEN & REGELN:\n"
                "1. ABSATZ-STRUKTUR & LISTEN:\n"
                "   - Beginne mit 1 bis maximal 2 kurzen Einleitungssätzen (jeweils mit doppeltem Zeilenumbruch \\n\\n abgetrennt), damit die Sprachausgabe sofort starten kann.\n"
                "   - Fasse danach den Hauptteil in längeren, natürlichen Absätzen zusammen.\n"
                "   - Halte Aufzählungen und Listenpunkte innerhalb desselben Absatzes zusammen (kein \\n\\n zwischen Listenpunkten).\n"
                "2. ZAHLEN & DATEN (STRIKT):\n"
                "   - Belasse alle Zahlen, Jahreszahlen, Versionsnummern, IP-Adressen und Datumsangaben IMMER als Ziffern (z. B. 2026, 3.12, 192.168.1.1, 15. April). Schreibe Zahlen NIEMALS in Worten aus!\n"
                "3. EMOJIS & SONDERZEICHEN (STRIKT):\n"
                "   - Entferne alle visuellen Deko-Emojis (wie 🎤, 🎧, 😃, 😢, 😎, 🐱, 🚀, 🍕, 🌟, 🌍, 🧠, 🐢) restlos aus dem Text. Es dürfen KEINE rohen Emojis im Text verbleiben!\n"
                "   - Wandle Keycap-Zahlen (1️⃣, 2️⃣) in normale Ziffern um (1., 2.).\n"
                "   - Ersetze funktionale Symbole phonetisch (z. B. ⚡ -> Blitz-Symbol, 💡 -> Glühbirnen-Symbol, ✓ -> Häkchen, ✗ -> Kreuz, → -> Pfeil zu).\n"
                "4. WÄHRUNGEN & ABKÜRZUNGEN:\n"
                "   - Währungen nach dem Betrag ausschreiben (z. B. '1 250 000 Euro', '850 000 Dollar', '750 000 Pfund').\n"
                "   - Symbole & Einheiten ausschreiben (z. B. '%' -> 'Prozent', '°C' -> 'Grad Celsius', '& Co.' -> 'und Co.').\n"
                "   - Abkürzungen ausschreiben (z. B. 'z. B.' -> 'zum Beispiel', 'd. h.' -> 'das heißt', 'bzw.' -> 'beziehungsweise', 'ca.' -> 'circa', 'usw.' -> 'und so weiter', 'ms' -> 'Millisekunden').\n"
                "   - Satzzeichen (Punkt, Komma, Doppelpunkt) NIEMALS als Wörter buchstabieren.\n"
                "5. Gib ausschließlich den formatierten Originaltext aus, ohne jede Einleitung oder Erklärung."
            ),
            description="System prompt for the task model."
        )

    def __init__(self):
        self.valves = self.Valves()

    def _sanitize_and_clean(self, text: str) -> str:
        """Deterministic phonetic, emoji and markdown sanitizer."""
        # 1. Clean keycap numbers 1️⃣ -> 1., 2️⃣ -> 2., etc.
        keycaps = {
            '1️⃣': '1.', '2️⃣': '2.', '3️⃣': '3.', '4️⃣': '4.', '5️⃣': '5.',
            '6️⃣': '6.', '7️⃣': '7.', '8️⃣': '8.', '9️⃣': '9.', '🔟': '10.',
            '0️⃣': '0.', '1\ufe0f\u20e3': '1.', '2\ufe0f\u20e3': '2.', '3\ufe0f\u20e3': '3.',
            '4\ufe0f\u20e3': '4.', '5\ufe0f\u20e3': '5.', '6\ufe0f\u20e3': '6.', '7\ufe0f\u20e3': '7.',
            '8\ufe0f\u20e3': '8.', '9\ufe0f\u20e3': '9.', '🔟\ufe0f': '10.',
            '#️⃣': '#', '*️⃣': '*'
        }
        for k, v in keycaps.items():
            text = text.replace(k, v)

        # 2. Named functional symbols
        named_symbols = [
            (r'⚡', ' Blitz-Symbol '),
            (r'💡', ' Glühbirnen-Symbol '),
            (r'[✓✔]', ' Häkchen '),
            (r'[✗✖❌]', ' Kreuz '),
            (r'©', ' Copyright '),
            (r'™', ' Trademark '),
            (r'®', ' Registered '),
            (r'->|➔|→', ' Pfeil zu '),
            (r'#([A-Za-z0-9äöüÄÖÜ_]+)', r'Hashtag \1'),
            (r'&\s*Co\.', 'und Co.'),
            (r'\b&\b', 'und'),
        ]
        for pattern, repl in named_symbols:
            text = re.sub(pattern, repl, text)

        # 3. Universal Emoji & Pictograph Stripping
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs (earth, cat, rocket, pizza, star, etc.)
            "\U0001F680-\U0001F6FF"  # Transport & Map
            "\U0001F700-\U0001F77F"  # Alchemical Symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols (brain, turtle, etc.)
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols & Pictographs Extended
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251"  # Enclosed Characters
            "\U0001F004-\U0001F0CF"  # Playing cards / Mahjong
            "\U00002600-\U000026FF"  # Misc Symbols
            "\U00002B00-\U00002BFF"  # Misc Symbols & Arrows
            "\U0000FE00-\U0000FE0F"  # Variation Selectors
            "\U000020D0-\U000020FF"  # Combining Diacritical Marks for Symbols
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)

        # 4. Clean markdown headers and horizontal rules
        text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

        # 5. Strip inline markdown styling (bold, italic, code)
        if self.valves.clean_markdown:
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            text = re.sub(r'__([^_]+)__', r'\1', text)
            text = re.sub(r'_([^_]+)_', r'\1', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)

        # 6. Currencies: Move currency symbol AFTER digits/scale words, keeping digits intact
        scale_units = r'(?:\s*(?:million|billion|trillion|mio|mrd|millionen|milliarden|tausend|thousand))?'
        text = re.sub(r'€\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Euro', text, flags=re.IGNORECASE)
        text = re.sub(r'\$\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Dollar', text, flags=re.IGNORECASE)
        text = re.sub(r'£\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Pfund', text, flags=re.IGNORECASE)
        text = re.sub(r'¥\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Yen', text, flags=re.IGNORECASE)
        text = re.sub(r'€', ' Euro ', text)
        text = re.sub(r'\$', ' Dollar ', text)
        text = re.sub(r'£', ' Pfund ', text)
        text = re.sub(r'¥', ' Yen ', text)

        # 7. Units & Percent
        text = re.sub(r'%\s*', ' Prozent ', text)
        text = re.sub(r'°\s*C\b', ' Grad Celsius', text)
        text = re.sub(r'°\s*F\b', ' Grad Fahrenheit', text)
        text = re.sub(r'§\s*', ' Paragraph ', text)

        # 8. Common abbreviations
        abbreviations = [
            (r'\bz\.B\.', 'zum Beispiel'),
            (r'\bz\.\s*B\.', 'zum Beispiel'),
            (r'\bd\.h\.', 'das heißt'),
            (r'\bd\.\s*h\.', 'das heißt'),
            (r'\bu\.a\.', 'unter anderem'),
            (r'\bu\.\s*a\.', 'unter anderem'),
            (r'\bbzw\.', 'beziehungsweise'),
            (r'\bca\.', 'circa'),
            (r'\busw\.', 'und so weiter'),
            (r'\bevtl\.', 'eventuell'),
            (r'\bggf\.', 'gegebenenfalls'),
            (r'\bDr\.', 'Doktor'),
            (r'\bProf\.', 'Professor'),
            (r'\bNr\.', 'Nummer'),
            (r'\bvs\.', 'versus'),
            (r'\be\.g\.', 'for example'),
            (r'\bi\.e\.', 'that is'),
            (r'\betc\.', 'et cetera'),
            (r'\bms\b', 'Millisekunden'),
            (r'\bkm/h\b', 'Kilometer pro Stunde'),
        ]
        for pattern, repl in abbreviations:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # 9. Normalize spaces
        text = text.replace('\u202f', ' ').replace('\u00a0', ' ')
        text = re.sub(r'[ \t]+', ' ', text)

        # 10. List items: Keep bullet items together in single paragraph
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            l = line.strip()
            if not l:
                if cleaned_lines and cleaned_lines[-1] != '':
                    cleaned_lines.append('')
                continue
            cleaned_lines.append(l)
        
        text = '\n'.join(cleaned_lines)

        # 11. Paragraph Pacing: Split only the first 1-2 introductory sentences
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            first_para = paragraphs[0]
            if not first_para.startswith(('-', '•', '1.', '2.', '3.')):
                sents = re.split(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ„"])', first_para)
                if len(sents) >= 3:
                    new_start = [sents[0], sents[1]]
                    remainder = " ".join(sents[2:])
                    if remainder:
                        new_start.append(remainder)
                    paragraphs = new_start + paragraphs[1:]
                elif len(sents) == 2:
                    paragraphs = [sents[0], sents[1]] + paragraphs[1:]
            
            text = "\n\n".join(paragraphs)

        return text.strip()

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        """Outlet hook: post-processes assistant response for TTS speech output."""
        messages = body.get("messages", [])
        if not messages:
            return body

        assistant_msg = messages[-1]
        if assistant_msg.get("role") != "assistant":
            return body

        original_text = assistant_msg.get("content", "")
        if not original_text or len(original_text.strip()) < 30:
            return body

        if self.valves.debug:
            print(f"[TTS-FILTER] Outlet triggered for model '{self.valves.task_model}' at '{self.valves.task_api_url}'")
            print(f"[TTS-FILTER] Original message length: {len(original_text)} chars")

        if not self.valves.use_task_model:
            assistant_msg["content"] = self._sanitize_and_clean(original_text)
            if self.valves.debug:
                print("[TTS-FILTER] Rule-based optimization applied successfully.")
            return body

        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"TTS-Optimierung mit {self.valves.task_model}...",
                    "done": False,
                }
            })

        try:
            url = f"{self.valves.task_api_url.rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.valves.task_api_key}",
            }
            payload = {
                "model": self.valves.task_model,
                "messages": [
                    {"role": "system", "content": self.valves.custom_system_prompt},
                    {"role": "user", "content": original_text},
                ],
                "temperature": 0.1,
                "max_tokens": 4096,
                "stream": False,
            }

            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        rewritten_text = res_json["choices"][0]["message"]["content"].strip()
                        if rewritten_text:
                            assistant_msg["content"] = self._sanitize_and_clean(rewritten_text)
                            if self.valves.debug:
                                print(f"[TTS-FILTER SUCCESS] Rewritten length: {len(assistant_msg['content'])} chars")
                    else:
                        error_msg = await response.text()
                        if self.valves.debug:
                            print(f"[TTS-FILTER ERROR] HTTP {response.status}: {error_msg}")
                        assistant_msg["content"] = self._sanitize_and_clean(original_text)

        except Exception as e:
            if self.valves.debug:
                print(f"[TTS-FILTER EXCEPTION] Error connecting to task model: {e}")
            assistant_msg["content"] = self._sanitize_and_clean(original_text)

        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "TTS-Optimierung abgeschlossen",
                    "done": True,
                }
            })

        return body
