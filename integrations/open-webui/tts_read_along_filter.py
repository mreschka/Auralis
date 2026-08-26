"""
title: TTS Read-Along & Paragraph Optimizer
author: Markus
description: Optimizes assistant responses for 1:1 read-along TTS. Preserves exact wording, cleans visual Markdown, expands currencies/symbols/emojis, and structures the first 2-3 sentences into individual short paragraphs for instant playback.
version: 1.2.0
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
        mode: str = Field(
            default="outlet_task_model",
            description="Mode: 'outlet_task_model' (rewrites via task model) or 'inlet_prompt_injection' (instructs main model directly) or 'rule_based_only'."
        )
        task_model: str = Field(
            default="gemma3:4b",
            description="Fast task model for phonetic alignment (e.g. gemma3:4b, llama3.2:3b)."
        )
        task_api_url: str = Field(
            default="http://localhost:11434/v1",
            description="URL of the OpenAI/Ollama API endpoint (IMPORTANT: Must be explicitly configured in Valves; does not inherit global settings)."
        )
        task_api_key: str = Field(
            default="ollama",
            description="API key if required."
        )
        use_task_model: bool = Field(
            default=True,
            description="Use LLM for intelligent paragraph structuring and expansion (with deterministic fallback)."
        )
        clean_markdown: bool = Field(
            default=True,
            description="Use Markdown-aware cleaning (via markdown + BeautifulSoup) to strip visual markdown artifacts."
        )
        debug: bool = Field(
            default=True,
            description="Enable verbose debug logs in Open WebUI server output and UI status badges."
        )
        custom_system_prompt: str = Field(
            default=(
                "Du bist ein phonetischer Formatierer für Sprachsynthese mit 1:1-Mitlesbarkeit am Bildschirm.\n\n"
                "STRIKTE REGELN:\n"
                "1. KEINE INHALTSÄNDERUNG: Ändere keine Sätze, formuliere nichts um, erfinde nichts hinzu und lasse nichts weg. Der Nutzer liest den Text beim Hören am Bildschirm mit!\n"
                "2. ABSATZ-STRUKTUR (für Sofort-Wiedergabe in Open WebUI):\n"
                "   - Trenne den 1. Satz als eigenen kurzen Absatz mit doppeltem Zeilenumbruch (\\n\\n) ab.\n"
                "   - Trenne den 2. Satz als eigenen kurzen Absatz mit doppeltem Zeilenumbruch (\\n\\n) ab.\n"
                "   - Trenne den 3. Satz als eigenen kurzen Absatz mit doppeltem Zeilenumbruch (\\n\\n) ab.\n"
                "   - Der verbleibende Haupttext bleibt in seinen normalen, zusammenhängenden Absätzen.\n"
                "3. SPRECHBARKEIT & PHONETIK:\n"
                "   - Währungen nach Betrag ausschreiben ('€ 1 250 000' -> '1 250 000 Euro', '$ 3.7 billion' -> '3.7 billion Dollar', '£ 750 000' -> '750 000 Pfund').\n"
                "   - Symbole & Einheiten ausschreiben ('%' -> 'Prozent', '°C' -> 'Grad Celsius', '& Co.' -> 'und Co.').\n"
                "   - Emojis & Sonderzeichen ausschreiben ('⚡' -> 'Blitz-Symbol', '💡' -> 'Glühbirnen-Symbol', '✓' -> 'Häkchen', '✗' -> 'Kreuz', '©' -> 'Copyright', '™' -> 'Trademark', '#Thema' -> 'Hashtag Thema').\n"
                "   - Abkürzungen ausschreiben ('z. B.' -> 'zum Beispiel', 'd. h.' -> 'das heißt', 'bzw.' -> 'beziehungsweise', 'ca.' -> 'circa', 'usw.' -> 'und so weiter', 'ms' -> 'Millisekunden').\n"
                "   - Nummerierte Listenpunkte fließend formatieren ('1.' -> 'Erstens:', '2.' -> 'Zweitens:', '3.' -> 'Drittens:').\n"
                "4. Gib ausschließlich den formatierten Originaltext aus, ohne jede Einleitung oder Begleittext."
            ),
            description="System prompt for the 1:1 read-along TTS optimizer."
        )

    def __init__(self):
        self.valves = self.Valves()

    def _sanitize_and_clean(self, text: str) -> str:
        """Two-tier sanitizer: Phonetic expansions + Markdown-aware structural cleaning."""
        # 1. Phonetic expansions: Currencies with numbers and scale units
        scale_units = r'(?:\s*(?:million|billion|trillion|mio|mrd|millionen|milliarden|tausend|thousand))?'
        text = re.sub(r'€\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Euro ', text, flags=re.IGNORECASE)
        text = re.sub(r'\$\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Dollar ', text, flags=re.IGNORECASE)
        text = re.sub(r'£\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Pfund ', text, flags=re.IGNORECASE)
        text = re.sub(r'¥\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Yen ', text, flags=re.IGNORECASE)
        text = re.sub(r'€', ' Euro ', text)
        text = re.sub(r'\$', ' Dollar ', text)
        text = re.sub(r'£', ' Pfund ', text)
        text = re.sub(r'¥', ' Yen ', text)

        # 2. Units & Percent
        text = re.sub(r'%\s*', ' Prozent ', text)
        text = re.sub(r'°\s*C\b', ' Grad Celsius', text)
        text = re.sub(r'°\s*F\b', ' Grad Fahrenheit', text)
        text = re.sub(r'§\s*', ' Paragraph ', text)

        # 3. Common Emojis & Symbols
        symbols = [
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
            (r'&', ' und '),
        ]
        for pattern, repl in symbols:
            text = re.sub(pattern, repl, text)

        # 4. Common abbreviations
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

        # 5. Markdown-aware cleaning
        if self.valves.clean_markdown:
            try:
                import markdown
                from bs4 import BeautifulSoup

                html_content = markdown.markdown(text, extensions=['extra', 'nl2br', 'sane_lists'])
                soup = BeautifulSoup(html_content, 'html.parser')

                # Format ordered list items
                for ol in soup.find_all('ol'):
                    for i, li in enumerate(ol.find_all('li', recursive=False), 1):
                        labels = {1: "Erstens:", 2: "Zweitens:", 3: "Drittens:", 4: "Viertens:", 5: "Fünftens:"}
                        label = labels.get(i, f"Punkt {i}:")
                        li.insert_before(f'\n{label} ')
                        li.unwrap()
                    ol.unwrap()

                # Format unordered list items
                for ul in soup.find_all('ul'):
                    for li in ul.find_all('li', recursive=False):
                        li.insert_before('\n- ')
                        li.unwrap()
                    ul.unwrap()

                # Separate block elements
                for block in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'blockquote']):
                    block.insert_after('\n\n')
                    block.unwrap()

                cleaned_text = soup.get_text()
            except Exception:
                # Deterministic Regex fallback
                cleaned_text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
                cleaned_text = re.sub(r'^#+\s*', '', cleaned_text, flags=re.MULTILINE)
                cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)
                cleaned_text = re.sub(r'\*([^*]+)\*', r'\1', cleaned_text)
                cleaned_text = re.sub(r'__([^_]+)__', r'\1', cleaned_text)
                cleaned_text = re.sub(r'_([^_]+)_', r'\1', cleaned_text)
                cleaned_text = re.sub(r'`([^`]+)`', r'\1', cleaned_text)
                cleaned_text = re.sub(r'^\s*1\.\s*', 'Erstens: ', cleaned_text, flags=re.MULTILINE)
                cleaned_text = re.sub(r'^\s*2\.\s*', 'Zweitens: ', cleaned_text, flags=re.MULTILINE)
                cleaned_text = re.sub(r'^\s*3\.\s*', 'Drittens: ', cleaned_text, flags=re.MULTILINE)
                cleaned_text = re.sub(r'^\s*4\.\s*', 'Viertens: ', cleaned_text, flags=re.MULTILINE)
                cleaned_text = re.sub(r'^\s*5\.\s*', 'Fünftens: ', cleaned_text, flags=re.MULTILINE)
        else:
            cleaned_text = text

        # 6. Normalize whitespaces
        cleaned_text = cleaned_text.replace('\u202f', ' ').replace('\u00a0', ' ')
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        # 7. Split first 2-3 sentences into distinct short paragraphs for instant TTFT (< 1s)
        paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]
        if paragraphs:
            first_para = paragraphs[0]
            sents = re.split(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9„"])', first_para)
            if len(sents) >= 3:
                new_start = [sents[0], sents[1]]
                remainder = " ".join(sents[2:])
                if remainder:
                    new_start.append(remainder)
                paragraphs = new_start + paragraphs[1:]
            elif len(sents) == 2:
                paragraphs = [sents[0], sents[1]] + paragraphs[1:]
            cleaned_text = "\n\n".join(paragraphs)

        return cleaned_text.strip()

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """Inlet hook: injects direct TTS formatting rules into the main prompt if in inlet mode."""
        if self.valves.mode != "inlet_prompt_injection":
            return body

        if self.valves.debug:
            print("[TTS-FILTER] Running INLET prompt injection...")

        instruction = (
            "\n\n[SYSTEM INSTRUKTION: TTS-FORMATIERUNG]\n"
            "Strukturiere deine Antwort für Absatz-basierte Sprachsynthese:\n"
            "1. Trenne die ersten 2 bis 3 Sätze jeweils als eigene kurze Absätze mit doppeltem Zeilenumbruch (\\n\\n) ab, damit die Sprachausgabe ohne Verzögerung starten kann.\n"
            "2. Schreibe danach ausführliche Absätze für den Hauptinhalt.\n"
            "3. Schreibe Abkürzungen wie z. B., bzw., d. h., usw., Währungen und Symbole wie %, €, $ immer vollständig als Wort aus."
        )

        messages = body.get("messages", [])
        if messages:
            if messages[0].get("role") == "system":
                messages[0]["content"] += instruction
            else:
                messages.insert(0, {"role": "system", "content": instruction})

        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        """Outlet hook: optimizes text for 1:1 read-along TTS."""
        if self.valves.mode == "inlet_prompt_injection":
            return body

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

        if self.valves.mode == "rule_based_only" or not self.valves.use_task_model:
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
                            # Apply final markdown & phonetic sanitization pass
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
