"""
title: TTS Read-Along & Paragraph Optimizer
author: Markus
description: Optimizes assistant responses for natural, low-latency TTS. Preserves digits/numbers exactly, groups bullet lists in single paragraphs, expands currencies/symbols/emojis, and ensures natural speech prosody.
version: 1.4.0
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
            default="inlet_prompt_injection",
            description="Mode: 'inlet_prompt_injection' (recommended for live streaming/auto-play) or 'outlet_task_model' (post-generation rewrite) or 'rule_based_only'."
        )
        task_model: str = Field(
            default="gemma3:4b",
            description="Fast task model for phonetic alignment in outlet mode (e.g. gemma3:4b, llama3.2:3b)."
        )
        task_api_url: str = Field(
            default="http://localhost:11434/v1",
            description="URL of the OpenAI/Ollama API endpoint (only used in outlet mode; must be explicitly configured in Valves)."
        )
        task_api_key: str = Field(
            default="ollama",
            description="API key if required."
        )
        clean_markdown: bool = Field(
            default=True,
            description="Strips visual Markdown formatting (**, __, code blocks, horizontal rules) for clean TTS speech."
        )
        debug: bool = Field(
            default=True,
            description="Enable verbose debug logs in Open WebUI server output."
        )
        custom_system_prompt: str = Field(
            default=(
                "Du bist ein phonetischer Formatierer für Sprachsynthese mit 1:1-Mitlesbarkeit am Bildschirm.\n\n"
                "STRIKTE REGELN:\n"
                "1. KEINE INHALTSÄNDERUNG: Ändere keine Formulierungen und formuliere nichts um. Der Nutzer liest den Text beim Hören am Bildschirm mit!\n"
                "2. ZAHLEN & DATEN ALS ZIFFERN BELASSEN: Schreibe Zahlen, Jahreszahlen, Versionsnummern, IP-Adressen und Datumsangaben NIEMALS als Wörter aus! Belasse sie immer als Ziffern (z. B. 2026, 3.12, 192.168.1.1, 15. April).\n"
                "3. ABSATZ-STRUKTUR & LISTEN:\n"
                "   - Beginne mit 1 bis maximal 2 kurzen Einleitungssätzen (jeweils mit doppeltem Zeilenumbruch \\n\\n abgetrennt), damit die Sprachausgabe sofort starten kann.\n"
                "   - Halte den Hauptteil in längeren, gehaltvollen Absätzen zusammen.\n"
                "   - Halte Aufzählungen und Listenpunkte innerhalb desselben Absatzes zusammen (nur einfacher Zeilenumbruch \\n, KEIN doppelter \\n\\n zwischen Listenpunkten).\n"
                "4. SPRECHBARKEIT & PHONETIK:\n"
                "   - Währungen nach dem Betrag ausschreiben ('€ 1 250 000' -> '1 250 000 Euro', '$ 3.7 billion' -> '3.7 billion Dollar', '£ 750 000' -> '750 000 Pfund').\n"
                "   - Symbole & Einheiten ausschreiben ('%' -> 'Prozent', '°C' -> 'Grad Celsius', '& Co.' -> 'und Co.').\n"
                "   - Emojis & Sonderzeichen als Wort ausschreiben ('⚡' -> 'Blitz-Symbol', '💡' -> 'Glühbirnen-Symbol', '✓' -> 'Häkchen', '✗' -> 'Kreuz', '©' -> 'Copyright', '™' -> 'Trademark', '#Thema' -> 'Hashtag Thema').\n"
                "   - Abkürzungen ausschreiben ('z. B.' -> 'zum Beispiel', 'd. h.' -> 'das heißt', 'bzw.' -> 'beziehungsweise', 'ca.' -> 'circa', 'usw.' -> 'und so weiter', 'ms' -> 'Millisekunden').\n"
                "   - Satzzeichen (Punkt, Komma, Doppelpunkt) NIEMALS als Wörter buchstabieren, sondern als normale Satzzeichen belassen.\n"
                "5. Gib ausschließlich den formatierten Originaltext aus, ohne Einleitung oder Begleittext."
            ),
            description="System prompt for the 1:1 read-along TTS optimizer (used in outlet mode)."
        )

    def __init__(self):
        self.valves = self.Valves()

    def _sanitize_and_clean(self, text: str) -> str:
        """Deterministic, high-fidelity phonetic and markdown sanitizer."""
        # 1. Clean markdown headers and horizontal rules
        text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

        # 2. Strip inline markdown styling (bold, italic, code) without destroying text
        if self.valves.clean_markdown:
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^*]+)\*', r'\1', text)
            text = re.sub(r'__([^_]+)__', r'\1', text)
            text = re.sub(r'_([^_]+)_', r'\1', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)

        # 3. Currencies: Move currency symbol AFTER digits/scale words, keeping DIGITS UNTOUCHED
        scale_units = r'(?:\s*(?:million|billion|trillion|mio|mrd|millionen|milliarden|tausend|thousand))?'
        text = re.sub(r'€\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Euro', text, flags=re.IGNORECASE)
        text = re.sub(r'\$\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Dollar', text, flags=re.IGNORECASE)
        text = re.sub(r'£\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Pfund', text, flags=re.IGNORECASE)
        text = re.sub(r'¥\s*([0-9]+(?:[.,\s\u202f][0-9]+)*' + scale_units + r')', r'\1 Yen', text, flags=re.IGNORECASE)
        # Standalone currency symbols
        text = re.sub(r'€', ' Euro ', text)
        text = re.sub(r'\$', ' Dollar ', text)
        text = re.sub(r'£', ' Pfund ', text)
        text = re.sub(r'¥', ' Yen ', text)

        # 4. Units & Percent (keep numbers as digits!)
        text = re.sub(r'%\s*', ' Prozent ', text)
        text = re.sub(r'°\s*C\b', ' Grad Celsius', text)
        text = re.sub(r'°\s*F\b', ' Grad Fahrenheit', text)
        text = re.sub(r'§\s*', ' Paragraph ', text)

        # 5. Common Emojis & Symbols
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
            (r'\b&\b', 'und'),
        ]
        for pattern, repl in symbols:
            text = re.sub(pattern, repl, text)

        # 6. Abbreviations (expand only abbreviations, never touch digits/punctuation)
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

        # 7. Normalize spaces and narrow non-breaking spaces
        text = text.replace('\u202f', ' ').replace('\u00a0', ' ')
        text = re.sub(r'[ \t]+', ' ', text)

        # 8. List items formatting: Keep list items together within the same paragraph
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

        # 9. Paragraph Pacing: Split first 1-2 introductory sentences, keep everything else intact
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

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __model__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """Inlet hook: injects natural TTS formatting rules into the main prompt before streaming."""
        if self.valves.mode != "inlet_prompt_injection":
            return body

        if self.valves.debug:
            print("[TTS-FILTER] Running INLET prompt injection for natural live-stream TTS...")

        instruction = (
            "\n\n[SYSTEM INSTRUKTION: TTS-FORMATIERUNG FÜR LIVE-SPRACHAUSGABE]\n"
            "Strukturiere deine Antwort für natürliche Sprachausgabe:\n"
            "1. ABSATZ-STRUKTUR & LISTEN:\n"
            "   - Beginne mit 1 bis maximal 2 kurzen Einleitungssätzen (jeweils mit doppeltem Zeilenumbruch \\n\\n abgetrennt), damit die Sprachausgabe ohne Verzögerung starten kann.\n"
            "   - Fasse danach den Hauptteil in längeren, zusammenhängenden Absätzen zusammen.\n"
            "   - Halte Aufzählungen und Listenpunkte innerhalb desselben Absatzes zusammen (nur einfacher Zeilenumbruch \\n, KEIN doppelter \\n\\n zwischen Listenpunkten).\n"
            "2. ZAHLEN & DATEN ALS ZIFFERN BELASSEN:\n"
            "   - Belasse Zahlen, Jahreszahlen, Versionsnummern, IP-Adressen und Datumsangaben IMMER als Ziffern (z. B. 2026, 3.12, 192.168.1.1, 15. April). Schreibe Zahlen NIEMALS als Wörter aus!\n"
            "3. WÄHRUNGEN & SYMBOLE:\n"
            "   - Schreibe Währungen nach dem Betrag als Wort aus (z. B. '1 250 000 Euro', '850 000 Dollar', '750 000 Pfund').\n"
            "   - Schreibe Symbole und Einheiten aus (z. B. '%' -> 'Prozent', '°C' -> 'Grad Celsius', '& Co.' -> 'und Co.').\n"
            "   - Schreibe Emojis und Icons als kurzes Wort (z. B. '⚡' -> 'Blitz-Symbol', '💡' -> 'Glühbirnen-Symbol', '✓' -> 'Häkchen', '✗' -> 'Kreuz', '#Thema' -> 'Hashtag Thema').\n"
            "4. SATZZEICHEN & ABKÜRZUNGEN:\n"
            "   - Schreibe gebräuchliche Abkürzungen voll aus (z. B. 'z. B.' -> 'zum Beispiel', 'd. h.' -> 'das heißt', 'bzw.' -> 'beziehungsweise', 'ca.' -> 'circa', 'usw.' -> 'und so weiter').\n"
            "   - Schreibe Satzzeichen (Punkt, Komma, Doppelpunkt, Bindestrich) NIEMALS als Wörter aus – belasse sie als normale Satzzeichen für die natürliche Satzmelodie.\n"
            "   - Verzichte auf störende visuelle Markdown-Syntax (wie ***, ___, ###, ---)."
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
        """Outlet hook: optimizes text for 1:1 read-along TTS in non-streaming or post-completion modes."""
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
