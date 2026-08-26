"""
title: TTS Read-Along & Paragraph Optimizer
author: Markus
description: Optimizes assistant responses for natural, low-latency TTS. Translates emojis to text, restructures lists via task model, and ensures natural speech prosody.
version: 2.1.0
license: MIT
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable
import aiohttp
import re

# Muss im System installiert sein: pip install emoji
import emoji


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=10,
            description="Priority of this filter in the Open WebUI pipeline.",
        )
        use_task_model: bool = Field(
            default=True,
            description="Use fast LLM task model for paragraph restructuring.",
        )
        task_model: str = Field(
            default="gemma3:4b",
            description="Task model name (e.g. gemma3:4b, llama3.2:3b).",
        )
        task_api_url: str = Field(
            default="http://localhost:11434/v1",
            description="URL of the OpenAI/Ollama API endpoint.",
        )
        task_api_key: str = Field(default="ollama", description="API key if required.")
        clean_markdown: bool = Field(
            default=True,
            description="Strips visual Markdown formatting for clean speech.",
        )
        debug: bool = Field(
            default=True,
            description="Enable verbose debug logs in Open WebUI server output.",
        )
        custom_system_prompt: str = Field(
            default=(
                "Du bist ein Text-Optimierer für Sprachsynthese (TTS). WICHTIGSTE REGEL: Der Nutzer sieht den Originaltext auf dem Bildschirm und MUSS 1:1 mitlesen können! "
                "Du darfst den Text inhaltlich nicht zusammenfassen, keine Sätze weglassen und die grundlegende visuelle Struktur (Überschriften, Zeilenumbrüche) nicht zerstören.\n\n"
                "AUFGABEN & REGELN:\n"
                "1. STRUKTUR & MITLESBARKEIT:\n"
                "   - Behalte den genauen Wortlaut so weit wie möglich bei.\n"
                "   - Überschriften und nummerierte Listen (1., 2.) bleiben als Struktur erhalten. Erhalte die Absätze.\n"
                "2. LISTEN & BULLET-POINTS TTS-FREUNDLICH MACHEN:\n"
                "   - Entferne unlesbare Aufzählungszeichen wie Spiegelstriche (-), Sternchen (*) oder Rauten (#) am Zeilenanfang ersatzlos.\n"
                "   - Hänge an das Ende von kurzen Listenpunkten einen Punkt (.), damit die TTS-Engine eine natürliche Atempause macht.\n"
                "3. ZAHLEN & DATEN (STRIKT):\n"
                "   - Belasse alle Zahlen, Jahreszahlen (z.B. 2026) und Daten als Ziffern. Niemals als Text ausschreiben!\n"
                "4. EMOJIS & SYMBOLE:\n"
                "   - Emojis wurden bereits vom System in Text übersetzt (z.B. 'Lachendes Gesicht'). Lass diese Wörter im Text stehen, sie sollen mitgelesen werden.\n"
                "   - Ersetze funktionale Symbole (->, =>, ≈) durch passende Wörter im Kontext (z.B. 'entspricht', 'steht für', 'bedeutet'). Nicht wörtlich als 'Pfeil' übersetzen.\n"
                "5. WÄHRUNGEN & ABKÜRZUNGEN:\n"
                "   - Schreibe Einheiten aus ('€' -> 'Euro', '%' -> 'Prozent', 'Mio' -> 'Millionen').\n"
                "   - Schreibe Abkürzungen aus ('z. B.', 'bzw.', 'ca.').\n"
                "6. Gib ausschließlich den optimierten Text aus, ohne jede Einleitung, Bestätigung oder Erklärung."
            ),
            description="System prompt for the task model.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _sanitize_and_clean(self, text: str, user_lang: str = "de") -> str:
        """Deterministic phonetic, emoji and markdown sanitizer."""

        # 1. Clean keycaps (behalten wir, damit '1.' und nicht 'Taste 1' vorgelesen wird)
        keycaps = {
            "1️⃣": "1.",
            "2️⃣": "2.",
            "3️⃣": "3.",
            "4️⃣": "4.",
            "5️⃣": "5.",
            "6️⃣": "6.",
            "7️⃣": "7.",
            "8️⃣": "8.",
            "9️⃣": "9.",
            "🔟": "10.",
            "0️⃣": "0.",
            "1\ufe0f\u20e3": "1.",
            "2\ufe0f\u20e3": "2.",
            "3\ufe0f\u20e3": "3.",
            "4\ufe0f\u20e3": "4.",
            "5\ufe0f\u20e3": "5.",
            "6\ufe0f\u20e3": "6.",
            "7\ufe0f\u20e3": "7.",
            "8\ufe0f\u20e3": "8.",
            "9\ufe0f\u20e3": "9.",
            "🔟\ufe0f": "10.",
            "#️⃣": "#",
            "*️⃣": "*",
        }
        for k, v in keycaps.items():
            text = text.replace(k, v)

        # 2. Emojis per Library in Text übersetzen
        try:
            text = emoji.demojize(text, language=user_lang)
        except Exception as e:
            if self.valves.debug:
                print(
                    f"[TTS-FILTER] Emoji language '{user_lang}' not supported, fallback to 'en'. Error: {e}"
                )
            text = emoji.demojize(text, language="en")

        # Die Library macht aus 🚀 -> :Rakete: oder :rocket:
        # Wir entfernen die Doppelpunkte und ersetzen Unterstriche durch Leerzeichen für sauberes TTS
        text = re.sub(
            r":([a-zA-Z0-9äöüÄÖÜß_]+):",
            lambda m: " " + m.group(1).replace("_", " ") + " ",
            text,
        )

        # 3. Sonderzeichen für TTS bereinigen (verhindert, dass das LLM sie kopiert)
        text = text.replace("→", " bedeutet ")
        text = text.replace("≈", " ungefähr ")
        text = text.replace("=>", " daraus folgt ")

        # 4. Clean markdown headers, blockquotes, and horizontal rules
        text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

        # 5. Strip inline markdown styling (ohne Mathe-Operatoren zu killen!)
        if self.valves.clean_markdown:
            text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
            # Entfernt Kursiv-Sternchen NUR, wenn kein Leerzeichen direkt daneben steht
            text = re.sub(r"\*(?!\s)([^*]+?)(?<!\s)\*", r"\1", text)
            text = re.sub(r"`([^`]+)`", r"\1", text)

        # 6. Leerzeichen normalisieren und Absätze auf max. 2 Umbrüche begrenzen
        text = text.replace("\u202f", " ").replace("\u00a0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

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

        # Sprachende-Erkennung aus Open WebUI __user__
        user_lang = "de"
        if __user__:
            try:
                # Open WebUI speichert das typischerweise als 'de-DE' oder 'en-US'
                raw_lang = (
                    __user__.get("settings", {}).get("ui", {}).get("language", "")
                )
                if not raw_lang:
                    # Fallback für ältere Open WebUI Versionen
                    raw_lang = __user__.get("ui", {}).get("language", "")

                if raw_lang:
                    # Holt sich nur den ersten Teil (z.B. 'de' aus 'de-DE')
                    user_lang = raw_lang.split("-")[0].lower()
            except Exception:
                pass

        # Validierung, ob die Sprache von der emoji Library unterstützt wird
        supported_emoji_langs = [
            "en",
            "es",
            "pt",
            "it",
            "fr",
            "de",
            "ja",
            "ko",
            "zh",
            "ru",
            "ar",
        ]
        if user_lang not in supported_emoji_langs:
            user_lang = "de"

        if self.valves.debug:
            print(f"[TTS-FILTER] Outlet triggered for model '{self.valves.task_model}'")
            print(f"[TTS-FILTER] Detected user language for Emojis: {user_lang}")

        if not self.valves.use_task_model:
            assistant_msg["content"] = self._sanitize_and_clean(
                original_text, user_lang
            )
            return body

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"TTS-Optimierung mit {self.valves.task_model}...",
                        "done": False,
                    },
                }
            )

        try:
            # Markdown und Emojis strippen/übersetzen, bevor es ans Task-Modell geht
            pre_cleaned_text = self._sanitize_and_clean(original_text, user_lang)

            url = f"{self.valves.task_api_url.rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.valves.task_api_key}",
            }
            payload = {
                "model": self.valves.task_model,
                "messages": [
                    {"role": "system", "content": self.valves.custom_system_prompt},
                    {"role": "user", "content": pre_cleaned_text},
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
                        rewritten_text = res_json["choices"][0]["message"][
                            "content"
                        ].strip()
                        if rewritten_text:
                            # Whitespaces nach dem LLM sicherheitshalber nochmal normalisieren
                            assistant_msg["content"] = self._sanitize_and_clean(
                                rewritten_text, user_lang
                            )
                    else:
                        if self.valves.debug:
                            print(
                                f"[TTS-FILTER ERROR] HTTP {response.status}: {await response.text()}"
                            )
                        assistant_msg["content"] = pre_cleaned_text

        except Exception as e:
            if self.valves.debug:
                print(f"[TTS-FILTER EXCEPTION] Error connecting to task model: {e}")
            assistant_msg["content"] = self._sanitize_and_clean(
                original_text, user_lang
            )

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "TTS-Optimierung abgeschlossen",
                        "done": True,
                    },
                }
            )

        return body
