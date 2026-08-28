"""Comprehensive i18n/l10n localization registry for Auralis TTS Normalizer."""

from typing import Dict, List, Tuple

# Supported languages in XTTS-v2
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
            "Summarize the following code block in 1-2 concise sentences in English for text-to-speech reading (what does this code do?). "
            "Output ONLY the 1-2 spoken sentences, without introduction, quotes, or markdown.\n\nCode:\n{code}"
        ),
        "symbols": [
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
        "task_prompt": (
            "Eres un asistente de audio. "
            "Resume el siguiente bloque de código en 1-2 frases concisas en español para lectura de voz (¿qué hace este código?). "
            "Escribe ÚNICAMENTE las 1-2 frases habladas, sin introducción ni markdown.\n\nCódigo:\n{code}"
        ),
        "symbols": [
            (r'⚡', ' símbolo de rayo '),
            (r'💡', ' símbolo de bombilla '),
            (r'[✓✔]', ' marca de verificación '),
            (r'[✗✖❌]', ' cruz '),
            (r'->|➔|→', ' significa '),
            (r'≈', ' aproximadamente '),
            (r'\b&\b', 'y'),
        ],
        "abbreviations": [
            (r'\bp\.ej\.', 'por ejemplo'),
            (r'\betc\.', 'etcétera'),
            (r'\bDr\.', 'Doctor'),
            (r'\bProf\.', 'Profesor'),
            (r'\bms\b', 'milisegundos'),
            (r'\bkm/h\b', 'kilómetros por hora'),
        ],
        "units": {
            "kg": "kilogramos",
            "km": "kilómetros",
            "lb": "libras",
            "percent": "por ciento",
            "celsius": "grados Celsius",
            "fahrenheit": "grados Fahrenheit",
            "paragraph": "párrafo",
            "euro": "euros",
            "dollar": "dólares",
            "pound": "libras",
            "yen": "yenes",
        },
        "months": {
            '1': 'enero', '01': 'enero', '2': 'febrero', '02': 'febrero', '3': 'marzo', '03': 'marzo',
            '4': 'abril', '04': 'abril', '5': 'mayo', '05': 'mayo', '6': 'junio', '06': 'junio',
            '7': 'julio', '07': 'julio', '8': 'agosto', '08': 'agosto', '9': 'septiembre', '09': 'septiembre',
            '10': 'octubre', '11': 'noviembre', '12': 'diciembre'
        }
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
        "task_prompt": (
            "Tu es un assistant audio. "
            "Résume le bloc de code suivant en 1-2 phrases concises en français pour la synthèse vocale (que fait ce code ?). "
            "Écris UNIQUEMENT les 1-2 phrases parlées, sans introduction ni markdown.\n\nCode :\n{code}"
        ),
        "symbols": [
            (r'⚡', ' symbole éclair '),
            (r'💡', ' symbole ampoule '),
            (r'[✓✔]', ' coche '),
            (r'[✗✖❌]', ' croix '),
            (r'->|➔|→', ' signifie '),
            (r'≈', ' environ '),
            (r'\b&\b', 'et'),
        ],
        "abbreviations": [
            (r'\bpar ex\.', 'par exemple'),
            (r'\bc\.-à-d\.', 'c’est-à-dire'),
            (r'\betc\.', 'et cætera'),
            (r'\bDr\.', 'Docteur'),
            (r'\bProf\.', 'Professeur'),
            (r'\bms\b', 'millisecondes'),
            (r'\bkm/h\b', 'kilomètres par heure'),
        ],
        "units": {
            "kg": "kilogrammes",
            "km": "kilomètres",
            "lb": "livres",
            "percent": "pour cent",
            "celsius": "degrés Celsius",
            "fahrenheit": "degrés Fahrenheit",
            "paragraph": "paragraphe",
            "euro": "euros",
            "dollar": "dollars",
            "pound": "livres",
            "yen": "yens",
        },
        "months": {
            '1': 'janvier', '01': 'janvier', '2': 'février', '02': 'février', '3': 'mars', '03': 'mars',
            '4': 'avril', '04': 'avril', '5': 'mai', '05': 'mai', '6': 'juin', '06': 'juin',
            '7': 'juillet', '07': 'juillet', '8': 'août', '08': 'août', '9': 'septembre', '09': 'septembre',
            '10': 'octobre', '11': 'novembre', '12': 'décembre'
        }
    },
    "it": {
        "code_summary_intro": "Riepilogo del codice {lang}:",
        "code_summary_intro_generic": "Riepilogo del codice:",
        "code_skipped": "Blocco di codice saltato.",
        "table_intro": "Tabella con {n} {cols_word}. Intestazioni: {headers}.",
        "table_row": "Riga {n}: {row}.",
        "col_singular": "colonna",
        "col_plural": "colonne",
        "image_prefix": "Immagine:",
        "done_prefix": "Completato:",
        "todo_prefix": "Da fare:",
        "task_prompt": (
            "Sei un assistente audio. "
            "Riassumi il seguente blocco di codice in 1-2 frasi concise in italiano per la sintesi vocale. "
            "Scrivi SOLO le 1-2 frasi parlate.\n\nCodice:\n{code}"
        ),
        "symbols": [
            (r'⚡', ' simbolo fulmine '),
            (r'💡', ' simbolo lampadina '),
            (r'->|➔|→', ' significa '),
            (r'≈', ' circa '),
            (r'\b&\b', 'e'),
        ],
        "abbreviations": [
            (r'\bad es\.', 'ad esempio'),
            (r'\betc\.', 'eccetera'),
            (r'\bDr\.', 'Dottore'),
            (r'\bProf\.', 'Professore'),
            (r'\bms\b', 'millisecondi'),
            (r'\bkm/h\b', 'chilometri orari'),
        ],
        "units": {
            "kg": "chilogrammi",
            "km": "chilometri",
            "lb": "libbre",
            "percent": "percento",
            "celsius": "gradi Celsius",
            "fahrenheit": "grados Fahrenheit",
            "paragraph": "paragrafo",
            "euro": "euro",
            "dollar": "dollari",
            "pound": "sterline",
            "yen": "yen",
        },
        "months": {
            '1': 'gennaio', '01': 'gennaio', '2': 'febbraio', '02': 'febbraio', '3': 'marzo', '03': 'marzo',
            '4': 'aprile', '04': 'aprile', '5': 'maggio', '05': 'maggio', '6': 'giugno', '06': 'giugno',
            '7': 'luglio', '07': 'luglio', '8': 'agosto', '08': 'agosto', '9': 'settembre', '09': 'settembre',
            '10': 'ottobre', '11': 'novembre', '12': 'dicembre'
        }
    },
    "pt": {
        "code_summary_intro": "Resumo do código {lang}:",
        "code_summary_intro_generic": "Resumo do código:",
        "code_skipped": "Bloco de código ignorado.",
        "table_intro": "Tabela com {n} {cols_word}. Cabeçalhos: {headers}.",
        "table_row": "Linha {n}: {row}.",
        "col_singular": "coluna",
        "col_plural": "colunas",
        "image_prefix": "Imagem:",
        "done_prefix": "Concluído:",
        "todo_prefix": "Pendente:",
        "task_prompt": (
            "Você é um assistente de áudio. "
            "Resuma o seguinte bloco de código em 1-2 frases concisas em português para leitura de voz. "
            "Escreva APENAS as 1-2 frases faladas.\n\nCódigo:\n{code}"
        ),
        "symbols": [
            (r'⚡', ' símbolo de raio '),
            (r'💡', ' símbolo de lâmpada '),
            (r'->|➔|→', ' significa '),
            (r'≈', ' aproximadamente '),
            (r'\b&\b', 'e'),
        ],
        "abbreviations": [
            (r'\bpor ex\.', 'por exemplo'),
            (r'\betc\.', 'etcétera'),
            (r'\bDr\.', 'Doutor'),
            (r'\bProf\.', 'Professor'),
            (r'\bms\b', 'milissegundos'),
            (r'\bkm/h\b', 'quilômetros por hora'),
        ],
        "units": {
            "kg": "quilogramas",
            "km": "quilômetros",
            "lb": "libras",
            "percent": "por cento",
            "celsius": "graus Celsius",
            "fahrenheit": "graus Fahrenheit",
            "paragraph": "parágrafo",
            "euro": "euros",
            "dollar": "dólares",
            "pound": "libras",
            "yen": "ienes",
        },
        "months": {
            '1': 'janeiro', '01': 'janeiro', '2': 'fevereiro', '02': 'fevereiro', '3': 'março', '03': 'março',
            '4': 'abril', '04': 'abril', '5': 'maio', '05': 'maio', '6': 'junho', '06': 'junio',
            '7': 'julho', '07': 'julho', '8': 'agosto', '08': 'agosto', '9': 'setembro', '09': 'setembro',
            '10': 'outubro', '11': 'novembro', '12': 'dezembro'
        }
    },
    "pl": {
        "code_summary_intro": "Podsumowanie kodu {lang}:",
        "code_summary_intro_generic": "Podsumowanie kodu:",
        "code_skipped": "Blok kodu pominięty.",
        "table_intro": "Tabela z {n} {cols_word}. Nagłówki: {headers}.",
        "table_row": "Wiersz {n}: {row}.",
        "col_singular": "kolumną",
        "col_plural": "kolumnami",
        "image_prefix": "Obraz:",
        "done_prefix": "Zrobione:",
        "todo_prefix": "Do zrobienia:",
        "task_prompt": "Jesteś asystentem audio. Podsumuj poniższy kod w 1-2 zwięzłych zdaniach po polsku.\n\nKod:\n{code}",
        "symbols": [(r'⚡', ' symbol błyskawicy '), (r'->|➔|→', ' oznacza '), (r'≈', ' około ')],
        "abbreviations": [(r'\bnp\.', 'na przykład'), (r'\btzn\.', 'to znaczy'), (r'\bitd\.', 'i tak dalej')],
        "units": {"kg": "kilogramów", "km": "kilometrów", "lb": "funtów", "percent": "procent", "euro": "euro", "dollar": "dolarów"},
        "months": {'1': 'stycznia', '2': 'lutego', '3': 'marca', '4': 'kwietnia', '5': 'maja', '6': 'czerwca', '7': 'lipca', '8': 'sierpnia', '9': 'września', '10': 'października', '11': 'listopada', '12': 'grudnia'}
    },
    "ru": {
        "code_summary_intro": "Краткое содержание кода {lang}:",
        "code_summary_intro_generic": "Краткое содержание кода:",
        "code_skipped": "Блок кода пропущен.",
        "table_intro": "Таблица с {n} {cols_word}. Заголовки: {headers}.",
        "table_row": "Строка {n}: {row}.",
        "col_singular": "колонкой",
        "col_plural": "колонками",
        "image_prefix": "Изображение:",
        "done_prefix": "Выполнено:",
        "todo_prefix": "К выполнению:",
        "task_prompt": "Вы аудио-ассистент. Кратко опишите следующий код в 1-2 предложениях на русском языке.\n\nКод:\n{code}",
        "symbols": [(r'⚡', ' символ молнии '), (r'->|➔|→', ' означает '), (r'≈', ' примерно ')],
        "abbreviations": [(r'\bт\.е\.', 'то есть'), (r'\bт\.к\.', 'так как'), (r'\bи т\.д\.', 'и так далее')],
        "units": {"kg": "килограмм", "km": "километров", "lb": "фунтов", "percent": "процентов", "euro": "евро", "dollar": "долларов"},
        "months": {'1': 'января', '2': 'февраля', '3': 'марта', '4': 'апреля', '5': 'мая', '6': 'июня', '7': 'июля', '8': 'августа', '9': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'}
    }
}


def get_locale(lang: str) -> Dict:
    """Retrieve localization settings for a given language code, falling back to English."""
    norm_lang = lang.lower().split('-')[0].split('_')[0]
    return LOCALES.get(norm_lang, LOCALES["en"])
