# Open WebUI ➔ Auralis TTS Integration & Read-Along Filter 🎧

This directory provides the **TTS Read-Along & Paragraph Optimizer Filter** for Open WebUI.

---

## 🎯 Purpose & Key Features

1. **1:1 Synchronous Read-Along:**  
   Preserves the assistant's exact original text without hallucinating or altering sentences, allowing users to comfortably read along on-screen while listening.
2. **Instant Playback via Paragraph Splitting (`\n\n`):**  
   Splits the first 2–3 sentences into individual short starter paragraphs.
   * When Open WebUI's **`Split on: Paragraphs`** setting is enabled, Paragraph 1 is sent immediately to Auralis ➔ **Speech playback starts in under 1 second!**
   * While paragraphs 1–3 are playing, Auralis leverages vLLM parallel batching (`max_concurrency: 8`) to generate the longer body text concurrently in the background.
3. **Phonetic & Pronunciation Expansions:**  
   Expands abbreviations (`e.g.` ➔ `for example`, `i.e.` ➔ `that is`, `z. B.` ➔ `zum Beispiel`, `bzw.` ➔ `beziehungsweise`) and symbols (`€` ➔ `Euro`, `$` ➔ `Dollar`, `%` ➔ `percent`, `°C` ➔ `degrees Celsius`).

---

## 🚀 Setup & Installation in Open WebUI

### Step 1: Import the Filter Function into Open WebUI
1. Open your Open WebUI instance (e.g. `http://localhost:3000` or your custom domain).
2. Navigate to **Workspace ➔ Functions** (or **Admin Panel ➔ Functions**).
3. Click the **`+` (Create Function)** button in the top right.
4. Set the function type to **`Filter`**.
5. Copy and paste the entire content of [`tts_read_along_filter.py`](tts_read_along_filter.py) into the code editor.
6. Click **Save**.

### Step 2: Configure Filter Valves (Settings)
Click the gear icon (Valves/Settings) next to the newly created filter function:

| Valve / Setting | Default | Description |
| :--- | :--- | :--- |
| **`use_task_model`** | `True` | Uses a fast local task model for intelligent paragraph pacing (with fast regex fallback) |
| **`task_model`** | `gemma3:4b` | Name of the task model (e.g. on Ollama / llama-server) |
| **`task_api_url`** | `http://localhost:11434/v1` | URL of the OpenAI/Ollama compatible API endpoint |
| **`task_api_key`** | `ollama` | API key if authentication is required |

### Step 3: Configure Open WebUI Audio Settings
1. Go to **Settings ➔ Audio ➔ TTS Settings** (or **Admin Panel ➔ Audio**).
2. Configure the following fields:
   * **TTS Engine:** `OpenAI`
   * **API Base URL:** `http://<your-auralis-ip>:8502/v1`
   * **API Key:** `dummy`
   * **TTS Model:** `xttsv2`
   * **Default Voice:** `anna-1` (or any voice file in `voices/` like `markus`, `marie`)
   * **Split on:** **`Paragraphs`** (or **`Punctuation`**)

### Step 4: Enable Filter for Chat Models
1. Go to **Workspace ➔ Models**.
2. Select your desired chat model (e.g. `Qwen`, `Llama`, etc.).
3. Under **Filters**, toggle on **`TTS Read-Along & Paragraph Optimizer`**.
4. Click **Save**.

---

## 🧪 Verification & Usage

1. Send a prompt in chat asking for an explanation or summary.
2. The model generates its response; the filter ensures the first 2–3 sentences form quick starter paragraphs and abbreviations are expanded.
3. Click the **Read Aloud (Speaker)** button (or enter Call Mode):
   * The first paragraph renders in **< 1 second**, starting voice playback immediately.
   * Remaining paragraphs stream seamlessly in the background with zero perceived latency.
