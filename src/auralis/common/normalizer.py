import hashlib
import json
import logging
import os
import re
import unicodedata
import urllib.request
from typing import Dict, List, Optional, Tuple

try:
    from auralis.common.i18n import get_locale, SUPPORTED_LANGUAGES
    from auralis.common.dictionary import load_pronunciations, DEFAULT_PRONUNCIATIONS
except ImportError:
    from i18n_v2 import get_locale, SUPPORTED_LANGUAGES
    from dictionary import load_pronunciations, DEFAULT_PRONUNCIATIONS

try:
    from markdown_it import MarkdownIt
    HAS_MARKDOWN_IT = True
except ImportError:
    HAS_MARKDOWN_IT = False

try:
    import emoji
    HAS_EMOJI = True
except ImportError:
    HAS_EMOJI = False

logger = logging.getLogger(__name__)


class TextNormalizer:
    """High-performance AST-based Markdown & multilingual phonetic text normalizer for Auralis TTS.
    
    Features:
    - Multi-language support (de, en, es, fr, it, pt, pl, ru, nl, etc.)
    - AST-based Markdown transformation inspired by Robin-Reiche/markdown-read-aloud
    - Task-model 1-sentence code summarization in the requested language via local Ollama
    - Deterministic 0ms spoken table formatting with localized headers and row counters
    - Robust ordered list numbering (1), 2), 3)) and intonation protection
    - Localized date expansions, units, currencies, technical pronunciations, and emojis
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        default_lang: Optional[str] = None,
        clean_markdown: bool = True,
        enable_llm_summary: Optional[bool] = None,
        ollama_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        pronunciations: Optional[Dict[str, str]] = None,
    ):
        if enabled is None:
            enabled = os.getenv("AURALIS_ENABLE_NORMALIZER", "true").lower() in ("true", "1", "yes")
        self.enabled = enabled
        self.default_lang = default_lang or os.getenv("AURALIS_NORMALIZER_LANG", "de")
        self.clean_markdown = clean_markdown

        if enable_llm_summary is None:
            enable_llm_summary = os.getenv("AURALIS_ENABLE_LLM_SUMMARY", "true").lower() in ("true", "1", "yes")
        self.enable_llm_summary = enable_llm_summary
        self.ollama_url = (ollama_url or os.getenv("AURALIS_OLLAMA_URL", "http://172.17.0.1:11434")).rstrip('/')
        self.ollama_model = ollama_model or os.getenv("AURALIS_TASK_MODEL", "gemma3:4b")
        self._llm_cache: Dict[str, str] = {}

        # Initialize markdown-it parser
        if HAS_MARKDOWN_IT:
            try:
                self.md_parser = MarkdownIt('gfm-like').disable('linkify')
            except Exception:
                self.md_parser = MarkdownIt('commonmark').enable('table').enable('strikethrough')
        else:
            self.md_parser = None

        # Pre-compile emoji regex fallback
        self._emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
            "\U0001F680-\U0001F6FF"  # Transport & Map
            "\U0001F700-\U0001F77F"  # Alchemical
            "\U0001F780-\U0001F7FF"  # Geometric Shapes
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols
            "\U0001FA00-\U0001FA6F"  # Chess
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

        self._keycaps = {
            "1️⃣": "1.", "2️⃣": "2.", "3️⃣": "3.", "4️⃣": "4.", "5️⃣": "5.",
            "6️⃣": "6.", "7️⃣": "7.", "8️⃣": "8.", "9️⃣": "9.", "🔟": "10.",
            "0️⃣": "0.", "1\ufe0f\u20e3": "1.", "2\ufe0f\u20e3": "2.", "3\ufe0f\u20e3": "3.",
            "4\ufe0f\u20e3": "4.", "5\ufe0f\u20e3": "5.", "6\ufe0f\u20e3": "6.", "7\ufe0f\u20e3": "7.",
            "8\ufe0f\u20e3": "8.", "9\ufe0f\u20e3": "9.", "🔟\ufe0f": "10.",
            "#️⃣": "#", "*️⃣": "*"
        }

        # Technical pronunciation dictionary loaded from dictionary.py and optional custom JSON
        loaded_dict = load_pronunciations()
        if pronunciations:
            loaded_dict.update(pronunciations)
        self.pronunciations = loaded_dict

    def _call_task_model(self, prompt: str) -> Optional[str]:
        """Call local Ollama task model with a short timeout and caching."""
        cache_key = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]

        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 100
                }
            }
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                ans = res.get("response", "").strip()
                if ans:
                    ans = re.sub(r'^["\']|["\']$', '', ans).strip()
                    self._llm_cache[cache_key] = ans
                    return ans
        except Exception as e:
            logger.debug(f"[NORMALIZER] Task model call failed: {e}")
        return None

    def _summarize_code(self, code_full: str, lang_tag: str, target_lang: str, loc: Dict) -> str:
        lines = [l for l in code_full.strip().split('\n') if l.strip()]
        # For short CLI commands or 1-2 line snippets, speak directly in 0ms without waiting for LLM
        if len(lines) <= 2 or len(code_full.strip()) <= 90:
            content = " ".join(lines)
            is_cmd = lang_tag.lower() in ("cmd", "bash", "sh", "powershell", "zsh", "shell") or not lang_tag
            prefix = "Befehl:" if is_cmd and target_lang == "de" else ("Command:" if is_cmd else ("Code:" if target_lang == "de" else "Code:"))
            return f"{prefix} {content}"

        if self.enable_llm_summary:
            prompt = loc["task_prompt"].format(code=code_full)
            summary = self._call_task_model(prompt)
            if summary:
                logger.info(f"[NORMALIZER] Summarized code block via {self.ollama_model} ({target_lang}): '{summary}'")
                lang_display = lang_tag.capitalize() if lang_tag else ""
                if lang_display:
                    intro = loc["code_summary_intro"].format(lang=lang_display)
                else:
                    intro = loc["code_summary_intro_generic"]
                return f"{intro} {summary}"

        return loc["code_skipped"]

    def _render_inline_tokens(self, tokens: list, loc: Dict) -> str:
        """Recursively render inline tokens to natural spoken text."""
        out = []
        for t in tokens:
            if t.type == 'text':
                out.append(t.content)
            elif t.type == 'code_inline':
                out.append(t.content)
            elif t.type == 'image':
                alt = t.content or ''
                if alt:
                    out.append(f' {loc["image_prefix"]} {alt}. ')
            elif t.type in ('softbreak', 'hardbreak'):
                out.append(' ')
            elif t.type in ('link_open', 'link_close', 'strong_open', 'strong_close', 'em_open', 'em_close', 's_open', 's_close'):
                pass
            elif getattr(t, 'children', None):
                out.append(self._render_inline_tokens(t.children, loc))
            else:
                if getattr(t, 'content', None):
                    out.append(t.content)
        return ''.join(out)

    def _transform_markdown_ast(self, text: str, target_lang: str, loc: Dict) -> str:
        """Parse and transform Markdown AST into clean spoken text."""
        if not self.md_parser:
            return text

        # Strip reasoning / think tags before AST parsing
        text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<details[^>]*>[\s\S]*?</details>', '', text, flags=re.IGNORECASE)

        try:
            tokens = self.md_parser.parse(text)
        except Exception as e:
            logger.debug(f"[NORMALIZER] AST parse error: {e}, falling back to regex")
            return text

        blocks: List[str] = []
        list_stack: List[Dict] = []  # Track ordered/unordered list depth and counters
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.type == 'heading_open':
                inline_tok = tokens[i+1]
                t_text = self._render_inline_tokens(inline_tok.children or [inline_tok], loc).strip()
                if t_text:
                    blocks.append(t_text if t_text.endswith(('.', '!', '?', ':')) else t_text + '.')
                i += 3
                continue
            elif t.type == 'paragraph_open':
                inline_tok = tokens[i+1]
                t_text = self._render_inline_tokens(inline_tok.children or [inline_tok], loc).strip()
                if t_text:
                    blocks.append(t_text if t_text.endswith(('.', '!', '?', ':')) else t_text + '.')
                i += 3
                continue
            elif t.type == 'fence':
                lang_tag = t.info.strip()
                code_content = t.content.strip()
                summary_block = self._summarize_code(code_content, lang_tag, target_lang, loc)
                blocks.append(summary_block)
                i += 1
                continue
            elif t.type == 'table_open':
                headers = []
                rows = []
                cur_row = []
                i += 1
                while i < len(tokens) and tokens[i].type != 'table_close':
                    tok = tokens[i]
                    if tok.type in ('th_open', 'td_open'):
                        in_tok = tokens[i+1]
                        cell_txt = self._render_inline_tokens(in_tok.children or [in_tok], loc).strip()
                        cur_row.append(cell_txt)
                        i += 2
                    elif tok.type == 'tr_close':
                        if not headers:
                            headers = cur_row
                        else:
                            rows.append(cur_row)
                        cur_row = []
                        i += 1
                    else:
                        i += 1
                num_cols = len(headers)
                cols_word = loc["col_plural"] if num_cols != 1 else loc["col_singular"]
                header_str = ", ".join(headers)
                intro_str = loc["table_intro"].format(n=num_cols, cols_word=cols_word, headers=header_str)
                parts = [intro_str]
                for r_idx, r in enumerate(rows, 1):
                    row_str = ", ".join(r)
                    parts.append(loc["table_row"].format(n=r_idx, row=row_str))
                blocks.append(' '.join(parts))
                i += 1
                continue
            elif t.type == 'ordered_list_open':
                start_num = 1
                if t.attrs:
                    if isinstance(t.attrs, dict):
                        start_num = int(t.attrs.get('start', 1))
                    elif isinstance(t.attrs, list):
                        for item in t.attrs:
                            if isinstance(item, (list, tuple)) and len(item) == 2 and item[0] == 'start':
                                try:
                                    start_num = int(item[1])
                                except Exception:
                                    pass
                list_stack.append({'type': 'ol', 'count': start_num})
                i += 1
                continue
            elif t.type == 'ordered_list_close':
                if list_stack and list_stack[-1]['type'] == 'ol':
                    list_stack.pop()
                i += 1
                continue
            elif t.type == 'bullet_list_open':
                list_stack.append({'type': 'ul'})
                i += 1
                continue
            elif t.type == 'bullet_list_close':
                if list_stack and list_stack[-1]['type'] == 'ul':
                    list_stack.pop()
                i += 1
                continue
            elif t.type == 'list_item_open':
                # Collect item contents until list_item_close
                j = i + 1
                item_parts = []
                while j < len(tokens) and tokens[j].type != 'list_item_close':
                    if tokens[j].type == 'inline':
                        item_parts.append(self._render_inline_tokens(tokens[j].children or [tokens[j]], loc))
                    j += 1
                item_text = ' '.join(item_parts).strip()
                if item_text.startswith('[x] ') or item_text.startswith('[X] '):
                    item_text = f"{loc['done_prefix']} {item_text[4:]}"
                elif item_text.startswith('[ ] '):
                    item_text = f"{loc['todo_prefix']} {item_text[4:]}"
                elif list_stack and list_stack[-1]['type'] == 'ol':
                    count = list_stack[-1]['count']
                    item_text = f"{count}) {item_text}"
                    list_stack[-1]['count'] += 1
                if item_text:
                    blocks.append(item_text if item_text.endswith(('.', '!', '?', ':')) else item_text + '.')
                i = j + 1
                continue
            else:
                i += 1

        return '\n'.join(blocks)

    def _apply_pronunciations(self, text: str) -> str:
        """Apply pronunciation overrides for technical terms on word boundaries."""
        for key, spoken in self.pronunciations.items():
            pattern = rf'(?<![\w]){re.escape(key)}(?![\w])'
            text = re.sub(pattern, spoken, text, flags=re.IGNORECASE)
        return text

    def _normalize_dates(self, text: str, target_lang: str, loc: Dict) -> str:
        """Language-aware date expansion."""
        months = loc.get("months", {})
        if not months:
            return text

        if target_lang in ('de', 'pl', 'ru', 'nl'):
            def repl_dot_date(m: re.Match) -> str:
                d = int(m.group(1))
                mo = months.get(m.group(2), m.group(2))
                y = m.group(3)
                return f"{d}. {mo} {y}"
            text = re.sub(r'\b(0?[1-9]|[12][0-9]|3[01])\.(0?[1-9]|1[0-2])\.([12][0-9]{3})\b', repl_dot_date, text)

        elif target_lang in ('es', 'fr', 'it', 'pt'):
            def repl_slash_date(m: re.Match) -> str:
                d = int(m.group(1))
                mo = months.get(m.group(2), m.group(2))
                y = m.group(3)
                if target_lang in ('es', 'pt'):
                    return f"{d} de {mo} de {y}"
                return f"{d} {mo} {y}"
            text = re.sub(r'\b(0?[1-9]|[12][0-9]|3[01])[\/\-\.](0?[1-9]|1[0-2])[\/\-\.]([12][0-9]{3})\b', repl_slash_date, text)

        elif target_lang == 'en':
            def repl_en_iso_date(m: re.Match) -> str:
                y = m.group(1)
                mo = months.get(m.group(2), m.group(2))
                d = int(m.group(3))
                return f"{mo} {d}, {y}"
            text = re.sub(r'\b([12][0-9]{3})-(0?[1-9]|1[0-2])-(0?[1-9]|[12][0-9]|3[01])\b', repl_en_iso_date, text)

        return text

    def _normalize_units_and_currencies(self, text: str, loc: Dict) -> str:
        """Language-aware unit and currency symbol expansions."""
        u = loc.get("units", {})
        if not u:
            return text

        scale_units = r'(?:\s*(?:million|billion|trillion|mio|mrd|millionen|milliarden|tausend|thousand|millones|milliards))?'

        # Currencies
        if "euro" in u:
            text = re.sub(r'€\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', lambda m: f"{m.group(1)} {u['euro']}", text, flags=re.IGNORECASE)
            text = re.sub(r'€', f' {u["euro"]} ', text)
        if "dollar" in u:
            text = re.sub(r'\$\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', lambda m: f"{m.group(1)} {u['dollar']}", text, flags=re.IGNORECASE)
            text = re.sub(r'\$', f' {u["dollar"]} ', text)
        if "pound" in u:
            text = re.sub(r'£\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', lambda m: f"{m.group(1)} {u['pound']}", text, flags=re.IGNORECASE)
            text = re.sub(r'£', f' {u["pound"]} ', text)
        if "yen" in u:
            text = re.sub(r'¥\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', lambda m: f"{m.group(1)} {u['yen']}", text, flags=re.IGNORECASE)
            text = re.sub(r'¥', f' {u["yen"]} ', text)

        # Units
        if "percent" in u:
            text = re.sub(r'%\s*', f' {u["percent"]} ', text)
        if "celsius" in u:
            text = re.sub(r'°\s*C\b', f' {u["celsius"]}', text)
        if "fahrenheit" in u:
            text = re.sub(r'°\s*F\b', f' {u["fahrenheit"]}', text)
        if "paragraph" in u:
            text = re.sub(r'§\s*', f' {u["paragraph"]} ', text)
        if "lb" in u:
            text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*lb(?:s)?\b', rf'\1 {u["lb"]}', text, flags=re.IGNORECASE)
        if "kg" in u:
            text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*kg\b', rf'\1 {u["kg"]}', text, flags=re.IGNORECASE)
        if "km" in u:
            text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*km\b', rf'\1 {u["km"]}', text, flags=re.IGNORECASE)

        return text

    def normalize(self, text: str, lang: Optional[str] = None) -> str:
        """Normalize raw text for speech synthesis."""
        if not self.enabled or not text:
            return text

        target_lang = (lang or self.default_lang).lower()
        if '-' in target_lang:
            target_lang = target_lang.split('-')[0]

        loc = get_locale(target_lang)

        # 1. AST-based Markdown transformation
        if self.clean_markdown and self.md_parser:
            text = self._transform_markdown_ast(text, target_lang, loc)
        elif self.clean_markdown:
            text = re.sub(r'```[\s\S]*?```', f' {loc["code_skipped"]} ', text)
            text = re.sub(r'(?:^\|.*\|\r?\n)+', ' Tabelle übersprungen. ', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 2. Keycap numbers translation (1️⃣ -> 1.) before NFKC
        for k, v in self._keycaps.items():
            text = text.replace(k, v)

        # 3. Unicode Normalization (NFKC)
        text = unicodedata.normalize('NFKC', text)

        # 4. Non-breaking spaces and typography normalization
        text = re.sub(r'[\u00a0\u1680\u180e\u2000-\u200b\u202f\u205f\u3000\ufeff]', ' ', text)
        text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
        text = re.sub(r'[„“”«»\"\'`]', '', text)

        # 5. Named functional symbols for this locale (e.g. + -> plus)
        for pattern, repl in loc.get("symbols", []):
            text = re.sub(pattern, repl, text)

        # 6. Multilingual Emoji translation / demojize
        if HAS_EMOJI:
            try:
                supported_emoji_langs = ["en", "es", "pt", "it", "fr", "de", "ja", "ko", "zh", "ru", "ar"]
                emoji_lang = target_lang if target_lang in supported_emoji_langs else "en"
                text = emoji.demojize(text, language=emoji_lang)
                text = re.sub(r':(\w+):', lambda m: ' ' + m.group(1).replace('_', ' ') + ' ', text, flags=re.UNICODE)
            except Exception:
                text = self._emoji_pattern.sub('', text)
        else:
            text = self._emoji_pattern.sub('', text)

        # 7. Language-aware date normalization
        text = self._normalize_dates(text, target_lang, loc)

        # 8. Language-aware units and currencies
        text = self._normalize_units_and_currencies(text, loc)

        # 9. Language-aware abbreviations
        for pattern, repl in loc.get("abbreviations", []):
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # 10. Technical pronunciation overrides (nginx -> Engine X, k8s -> Kubernetes, etc.)
        text = self._apply_pronunciations(text)

        # 11. Whitespace & line-break cleanup
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n+', '\n', text).strip()

        # 12. Ensure sentence ends with punctuation to prevent XTTS hallucination/babbling on short fragments
        if text and not text.endswith(('.', '!', '?', ':', ';', ',')):
            text = text + '.'

        return text


# Global default instance
default_normalizer = TextNormalizer()


def normalize_text(text: str, lang: Optional[str] = None) -> str:
    """Convenience function to normalize text using the global TextNormalizer instance."""
    return default_normalizer.normalize(text, lang=lang)
