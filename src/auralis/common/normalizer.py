import os
import re
import unicodedata
from typing import Optional

try:
    import emoji
    HAS_EMOJI = True
except ImportError:
    HAS_EMOJI = False


class TextNormalizer:
    """High-performance text normalizer and phonetic pre-processor for Auralis TTS.
    
    Transforms raw text containing Markdown, emojis, currency symbols, dates, and abbreviations
    into clean, phonetically optimized text for XTTS-v2 inference.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        default_lang: Optional[str] = None,
        clean_markdown: bool = True,
    ):
        if enabled is None:
            enabled = os.getenv("AURALIS_ENABLE_NORMALIZER", "true").lower() in ("true", "1", "yes")
        self.enabled = enabled
        self.default_lang = default_lang or os.getenv("AURALIS_NORMALIZER_LANG", "de")
        self.clean_markdown = clean_markdown

        # Pre-compile emoji regex fallback
        self._emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
            "\U0001F680-\U0001F6FF"  # Transport & Map
            "\U0001F700-\U0001F77F"  # Alchemical
            "\U0001F780-\U0001F7FF"  # Geometric Shapes
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols (brain, turtle, etc.)
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

        self._named_symbols = [
            (r'⚡', ' Blitz-Symbol '),
            (r'💡', ' Glühbirnen-Symbol '),
            (r'[✓✔]', ' Häkchen '),
            (r'[✗✖❌]', ' Kreuz '),
            (r'©', ' Copyright '),
            (r'™', ' Trademark '),
            (r'®', ' Registered '),
            (r'->|➔|→', ' bedeutet '),
            (r'≈', ' ungefähr '),
            (r'=>', ' daraus folgt '),
            (r'#([A-Za-z0-9äöüÄÖÜ_]+)', r'Hashtag \1'),
            (r'&\s*Co\.', 'und Co.'),
            (r'\b&\b', 'und'),
        ]

        self._abbreviations = [
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

        self._months_de = {
            '01': 'Januar', '1': 'Januar',
            '02': 'Februar', '2': 'Februar',
            '03': 'März', '3': 'März',
            '04': 'April', '4': 'April',
            '05': 'Mai', '5': 'Mai',
            '06': 'Juni', '6': 'Juni',
            '07': 'Juli', '7': 'Juli',
            '08': 'August', '8': 'August',
            '09': 'September', '9': 'September',
            '10': 'Oktober',
            '11': 'November',
            '12': 'Dezember'
        }

    def _replace_date_de(self, m: re.Match) -> str:
        day = int(m.group(1))
        month = self._months_de.get(m.group(2), m.group(2))
        year = m.group(3)
        return f"{day}. {month} {year}"

    def normalize(self, text: str, lang: Optional[str] = None) -> str:
        """Normalize raw text for speech synthesis."""
        if not self.enabled or not text:
            return text

        target_lang = (lang or self.default_lang).lower()
        if '-' in target_lang:
            target_lang = target_lang.split('-')[0]

        # 1. Keycap numbers translation (1️⃣ -> 1.) before NFKC
        for k, v in self._keycaps.items():
            text = text.replace(k, v)

        # 2. Named functional symbols
        for pattern, repl in self._named_symbols:
            text = re.sub(pattern, repl, text)

        # 3. Multilingual Emoji translation / demojize
        if HAS_EMOJI:
            try:
                supported_emoji_langs = ["en", "es", "pt", "it", "fr", "de", "ja", "ko", "zh", "ru", "ar"]
                emoji_lang = target_lang if target_lang in supported_emoji_langs else "de"
                text = emoji.demojize(text, language=emoji_lang)
                text = re.sub(r':([a-zA-Z0-9äöüÄÖÜß_]+):', lambda m: ' ' + m.group(1).replace('_', ' ') + ' ', text)
            except Exception:
                text = self._emoji_pattern.sub('', text)
        else:
            text = self._emoji_pattern.sub('', text)

        # 4. Unicode Normalization (NFKC)
        text = unicodedata.normalize('NFKC', text)

        # 5. Non-breaking spaces and typography normalization
        text = re.sub(r'[\u00a0\u1680\u180e\u2000-\u200b\u202f\u205f\u3000\ufeff]', ' ', text)
        text = re.sub(r'[\u2010-\u2015\u2212]', '-', text)
        text = re.sub(r'[„“”«»\"\'`]', '', text)

        # 6. Markdown cleaning (preserving math operators)
        if self.clean_markdown:
            # Code blocks -> audible notice
            code_notice = ' Code-Block übersprungen. ' if target_lang == 'de' else ' Code block skipped. '
            text = re.sub(r'```[\s\S]*?```', code_notice, text)
            text = re.sub(r'```', '', text)

            # Markdown tables -> audible notice
            table_notice = ' Tabelle übersprungen. ' if target_lang == 'de' else ' Table skipped. '
            text = re.sub(r'(?:^\|.*\|\r?\n)+', table_notice, text, flags=re.MULTILINE)

            text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*>\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'\*(?!\s)([^*]+?)(?<!\s)\*', r'\1', text)
            text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
            text = re.sub(r'~~([^~]+)~~', r'\1', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            text = re.sub(r'(?m)^(\d+)\.\s*', r'\1) ', text)

        # 7. Dates (DD.MM.YYYY -> DD. Month YYYY) for German
        if target_lang == 'de':
            text = re.sub(r'\b(0?[1-9]|[12][0-9]|3[01])\.(0?[1-9]|1[0-2])\.([12][0-9]{3})\b', self._replace_date_de, text)

        # 8. Currencies: Move currency symbol AFTER digits/scale words, keeping digits intact
        scale_units = r'(?:\s*(?:million|billion|trillion|mio|mrd|millionen|milliarden|tausend|thousand))?'
        text = re.sub(r'€\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', r'\1 Euro', text, flags=re.IGNORECASE)
        text = re.sub(r'\$\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', r'\1 Dollar', text, flags=re.IGNORECASE)
        text = re.sub(r'£\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', r'\1 Pfund', text, flags=re.IGNORECASE)
        text = re.sub(r'¥\s*([0-9]+(?:[.,\s][0-9]+)*' + scale_units + r')', r'\1 Yen', text, flags=re.IGNORECASE)
        text = re.sub(r'€', ' Euro ', text)
        text = re.sub(r'\$', ' Dollar ', text)
        text = re.sub(r'£', ' Pfund ', text)
        text = re.sub(r'¥', ' Yen ', text)

        # 9. Units & Weights
        text = re.sub(r'%\s*', ' Prozent ', text)
        text = re.sub(r'°\s*C\b', ' Grad Celsius', text)
        text = re.sub(r'°\s*F\b', ' Grad Fahrenheit', text)
        text = re.sub(r'§\s*', ' Paragraph ', text)
        text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*lb(?:s)?\b', r'\1 Pfund', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*kg\b', r'\1 Kilogramm', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+(?:[.,]\d+)?)\s*km\b', r'\1 Kilometer', text, flags=re.IGNORECASE)

        # 10. Expand abbreviations
        for pattern, repl in self._abbreviations:
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        # 11. Whitespace cleanup
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
