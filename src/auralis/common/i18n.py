"""Comprehensive i18n/l10n localization registry for Auralis TTS Normalizer."""

from typing import Dict, List, Tuple

SUPPORTED_LANGUAGES = [
    "en", "de", "es", "fr", "it", "pt", "pl", "tr",
    "ru", "nl", "cs", "ar", "zh", "ja", "ko", "hu", "hi"
]

LOCALES: Dict[str, Dict] = {
    "de": {
        "code_summary_intro": "Zusammenfassung des {lang}-Codes:",
        "code_summary_intro_generic": "Zusammenfassung des Codes:",
        "code_skipped": "Code-Block übersprungen.",
        "table_intro": "Tabelle mit {n} {cols_word}. Überschriften: {headers}.",
        "table_row": "Zeile {n}: {row}.",
        "col_singular": "Spalte",
        "col_plural": "Spalten",
        "image_prefix": "Bild:",
        "done_prefix": "Erledigt:",
        "todo_prefix": "Offen:",
        "task_prompt": (
            "Du bist ein Audio-Assistent für Sprachausgabe. "
            "Fasse den folgenden Code-Block in 1-2 kurzen, prägnanten Sätzen auf Deutsch für das Vorlesen zusammen (was macht dieser Code?). "
            "Schreibe NUR die 1-2 gesprochenen Sätze, keine Einleitung, keine Anführungszeichen, kein Markdown.\n\nCode:\n{code}"
        ),
        "symbols": [
            (r'\s*\+\s*', ' plus '),
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
        ],
        "abbreviations": [
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
            (r'\bms\b', 'Millisekunden'),
            (r'\bkm/h\b', 'Kilometer pro Stunde'),
        ],
        "units": {
            "kg": "Kilogramm",
            "km": "Kilometer",
            "lb": "Pfund",
            "percent": "Prozent",
            "celsius": "Grad Celsius",
            "fahrenheit": "Grad Fahrenheit",
            "paragraph": "Paragraph",
            "euro": "Euro",
            "dollar": "Dollar",
            "pound": "Pfund",
            "yen": "Yen",
        },
        "months": {
            '1': 'Januar', '01': 'Januar', '2': 'Februar', '02': 'Februar', '3': 'März', '03': 'März',
            '4': 'April', '04': 'April', '5': 'Mai', '05': 'Mai', '6': 'Juni', '06': 'Juni',
            '7': 'Juli', '07': 'Juli', '8': 'August', '08': 'August', '9': 'September', '09': 'September',
            '10': 'Oktober', '11': 'November', '12': 'Dezember'
        }
    },
    "en": {
        "code_summary_intro": "Summary of the {lang} code:",
        "code_summary_intro_generic": "Summary of the code:",
        "code_skipped": "Code block skipped.",
        "table_intro": "Table with {n} {cols_word}. Headers: {headers}.",
        "table_row": "Row {n}: {row}.",
        "col_singular": "column",
        "col_plural": "columns",
        "image_prefix": "Image:",
        "done_prefix": "Done:",
        "todo_prefix": "Todo:",
        "task_prompt": (
            "You are an audio assistant. "
            "Summarize the following code block in 1-2 concise sentences in English for text-to-speech reading. "
            "Output ONLY the 1-2 spoken sentences.\n\nCode:\n{code}"
        ),
        "symbols": [
            (r'\s*\+\s*', ' plus '),
            (r'⚡', ' lightning symbol '),
            (r'💡', ' lightbulb symbol '),
            (r'[✓✔]', ' checkmark '),
            (r'[✗✖❌]', ' cross '),
            (r'©', ' copyright '),
            (r'™', ' trademark '),
            (r'®', ' registered '),
            (r'->|➔|→', ' means '),
            (r'≈', ' approximately '),
            (r'=>', ' implies '),
            (r'#([A-Za-z0-9_]+)', r'hashtag \1'),
            (r'\b&\b', 'and'),
        ],
        "abbreviations": [
            (r'\be\.g\.', 'for example'),
            (r'\be\.\s*g\.', 'for example'),
            (r'\bi\.e\.', 'that is'),
            (r'\bi\.\s*e\.', 'that is'),
            (r'\betc\.', 'et cetera'),
            (r'\bapprox\.', 'approximately'),
            (r'\bvs\.', 'versus'),
            (r'\bDr\.', 'Doctor'),
            (r'\bProf\.', 'Professor'),
            (r'\bNo\.', 'Number'),
            (r'\bms\b', 'milliseconds'),
            (r'\bmph\b', 'miles per hour'),
            (r'\bkm/h\b', 'kilometers per hour'),
        ],
        "units": {
            "kg": "kilograms",
            "km": "kilometers",
            "lb": "pounds",
            "percent": "percent",
            "celsius": "degrees Celsius",
            "fahrenheit": "degrees Fahrenheit",
            "paragraph": "section",
            "euro": "Euros",
            "dollar": "Dollars",
            "pound": "Pounds",
            "yen": "Yen",
        },
        "months": {
            '1': 'January', '01': 'January', '2': 'February', '02': 'February', '3': 'March', '03': 'March',
            '4': 'April', '04': 'April', '5': 'May', '05': 'May', '6': 'June', '06': 'June',
            '7': 'July', '07': 'July', '8': 'August', '08': 'August', '9': 'September', '09': 'September',
            '10': 'October', '11': 'November', '12': 'December'
        }
    },
    "es": {
        "code_summary_intro": "Resumen del código {lang}:",
        "code_summary_intro_generic": "Resumen del código:",
        "code_skipped": "Bloque de código omitido.",
        "table_intro": "Tabla con {n} {cols_word}. Encabezados: {headers}.",
        "table_row": "Fila {n}: {row}.",
        "col_singular": "columna",
        "col_plural": "columnas",
        "image_prefix": "Imagen:",
        "done_prefix": "Hecho:",
        "todo_prefix": "Pendiente:",
        "task_prompt": "Eres un asistente de audio. Resume el código en 1-2 frases concisas en español.\n\nCódigo:\n{code}",
        "symbols": [(r'\s*\+\s*', ' más '), (r'⚡', ' símbolo de rayo '), (r'->|➔|→', ' significa '), (r'≈', ' aproximadamente '), (r'\b&\b', 'y')],
        "abbreviations": [(r'\bp\.ej\.', 'por ejemplo'), (r'\betc\.', 'etcétera'), (r'\bDr\.', 'Doctor'), (r'\bms\b', 'milisegundos')],
        "units": {"kg": "kilogramos", "km": "kilómetros", "lb": "libras", "percent": "por ciento", "euro": "euros", "dollar": "dólares"},
        "months": {'1': 'enero', '2': 'febrero', '3': 'marzo', '4': 'abril', '5': 'mayo', '6': 'junio', '7': 'julio', '8': 'agosto', '9': 'septiembre', '10': 'octubre', '11': 'noviembre', '12': 'diciembre'}
    },
    "fr": {
        "code_summary_intro": "Résumé du code {lang} :",
        "code_summary_intro_generic": "Résumé du code :",
        "code_skipped": "Bloc de code ignoré.",
        "table_intro": "Tableau de {n} {cols_word}. En-têtes : {headers}.",
        "table_row": "Ligne {n} : {row}.",
        "col_singular": "colonne",
        "col_plural": "colonnes",
        "image_prefix": "Image :",
        "done_prefix": "Fait :",
        "todo_prefix": "À faire :",
        "task_prompt": "Tu es un assistant audio. Résume le code en 1-2 phrases concises en français.\n\nCode :\n{code}",
        "symbols": [(r'\s*\+\s*', ' plus '), (r'⚡', ' symbole éclair '), (r'->|➔|→', ' signifie '), (r'≈', ' environ '), (r'\b&\b', 'et')],
        "abbreviations": [(r'\bpar ex\.', 'par exemple'), (r'\bc\.-à-d\.', 'c’est-à-dire'), (r'\betc\.', 'et cætera')],
        "units": {"kg": "kilogrammes", "km": "kilomètres", "lb": "livres", "percent": "pour cent", "euro": "euros", "dollar": "dollars"},
        "months": {'1': 'janvier', '2': 'février', '3': 'mars', '4': 'avril', '5': 'mai', '6': 'juin', '7': 'juillet', '8': 'août', '9': 'septembre', '10': 'octobre', '11': 'novembre', '12': 'décembre'}
    }
}


def get_locale(lang: str) -> Dict:
    """Retrieve localization settings for a given language code, falling back to German or English."""
    norm_lang = lang.lower().split('-')[0].split('_')[0]
    return LOCALES.get(norm_lang, LOCALES.get("de", LOCALES["en"]))
