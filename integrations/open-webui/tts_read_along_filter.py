"""
title: TTS Read-Along & Paragraph Optimizer
author: Markus
description: Optimizes assistant responses for 1:1 read-along TTS. Preserves exact wording, restructures the first 2-3 sentences into individual short paragraphs for instant playback, and expands abbreviations/symbols.
version: 1.1.0
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
            description="Priority of this filter in the pipeline."
        )
        task_model: str = Field(
            default="gemma3:4b",
            description="Fast task model for phonetic alignment (e.g. gemma3:4b, llama3.2:3b)."
        )
        task_api_url: str = Field(
            default="http://localhost:11434/v1",
            description="URL of the OpenAI/Ollama API endpoint."
        )
        task_api_key: str = Field(
            default="ollama",
            description="API key if required."
        )
        use_task_model: bool = Field(
            default=True,
            description="Use LLM for intelligent paragraph structuring and expansion (with rule-based fallback)."
        )
        custom_system_prompt: str = Field(
            default=(
                "Du bist ein phonetischer Text-Formatierer für Sprachsynthese mit 1:1-Mitlesbarkeit am Bildschirm.\n\n"
                "STRIKTE REGELN:\n"
                "1. KEINE INHALTSÄNDERUNG: Ändere keine Sätze, formuliere nichts um, erfinde nichts hinzu und lasse nichts weg. Der Nutzer liest den Text beim Hören am Bildschirm mit!\n"
                "2. ABSATZ-STRUKTUR (für Sofort-Wiedergabe in Open WebUI):\n"
                "   - Trenne den 1. Satz als eigenen kurzen Absatz mit doppeltem Zeilenumbruch (\\n\\n) ab.\n"
                "   - Trenne den 2. Satz als eigenen kurzen Absatz mit doppeltem Zeilenumbruch (\\n\\n) ab.\n"
                "   - Trenne den 3. Satz als eigenen kurzen Absatz mit doppeltem Zeilenumbruch (\\n\\n) ab.\n"
                "   - Der verbleibende Haupttext bleibt in seinen normalen, zusammenhängenden Absätzen.\n"
                "3. SPRECHBARKEIT (nur Abkürzungen & Symbole ausschreiben):\n"
                "   - 'z. B.' / 'z.B.' -> 'zum Beispiel'\n"
                "   - 'd. h.' / 'd.h.' -> 'das heißt'\n"
                "   - 'bzw.' -> 'beziehungsweise'\n"
                "   - 'u. a.' / 'u.a.' -> 'unter anderem'\n"
                "   - 'ca.' -> 'circa'\n"
                "   - 'usw.' -> 'und so weiter'\n"
                "   - '%' -> 'Prozent'\n"
                "   - '€' -> 'Euro'\n"
                "   - '$' -> 'Dollar'\n"
                "   - '°C' -> 'Grad Celsius'\n"
                "4. Gib ausschließlich den formatierten Text aus, ohne jede Einleitung oder Erklärung."
            ),
            description="System prompt for the 1:1 read-along TTS optimizer."
        )

    def __init__(self):
        self.valves = self.Valves()

    def _rule_based_optimizer(self, text: str) -> str:
        """Deterministic fast rule-based optimizer for abbreviations, symbols and paragraph splitting."""
        # 1. Expand abbreviations & symbols
        replacements = [
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
            (r'€\s*', ' Euro '),
            (r'\$\s*', ' Dollar '),
            (r'%\s*', ' Prozent '),
            (r'°C\b', ' Grad Celsius'),
        ]
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # 2. Extract first 2-3 sentences into separate short paragraphs if they are merged
        paragraphs = text.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            # Split first paragraph on sentence boundary
            sents = re.split(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9])', first_para)
            if len(sents) >= 3:
                # Turn first 2-3 sentences into standalone paragraphs
                new_start = [sents[0], sents[1]]
                remainder = " ".join(sents[2:])
                if remainder:
                    new_start.append(remainder)
                paragraphs = new_start + paragraphs[1:]
                text = "\n\n".join(p.strip() for p in paragraphs if p.strip())

        return text.strip()

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __model__: Optional[dict] = None,
    ) -> dict:
        """Outlet hook: optimizes text for 1:1 read-along TTS."""
        messages = body.get("messages", [])
        if not messages:
            return body

        assistant_msg = messages[-1]
        if assistant_msg.get("role") != "assistant":
            return body

        original_text = assistant_msg.get("content", "")
        if not original_text or len(original_text.strip()) < 30:
            return body

        if not self.valves.use_task_model:
            assistant_msg["content"] = self._rule_based_optimizer(original_text)
            return body

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
                "temperature": 0.1,  # Low temperature for strict 1:1 reproduction
                "max_tokens": 4096,
                "stream": False,
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        rewritten_text = res_json["choices"][0]["message"]["content"].strip()
                        if rewritten_text:
                            # Final sanity check & abbreviation expansion
                            assistant_msg["content"] = self._rule_based_optimizer(rewritten_text)
                    else:
                        assistant_msg["content"] = self._rule_based_optimizer(original_text)

        except Exception:
            # Fallback to rule-based optimizer if task model is unreachable
            assistant_msg["content"] = self._rule_based_optimizer(original_text)

        return body
