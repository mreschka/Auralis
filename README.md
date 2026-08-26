[![](https://dcbadge.limes.pink/api/server/https://discord.gg/BEMVTmcPEs)](https://discord.gg/https://discord.gg/BEMVTmcPEs)

# Auralis for Open WebUI 🌌 (/auˈralis/)

Transform text into natural speech (with voice cloning) at warp speed.

This is a fork of the original Auralis optimized for Open WebUI and other interactive chat frameworks. 
I tried to minimited latency as far as possible and minimize the overhead in Open WebUI.

---

## What is special about this Auralis Fork? 🚀

Auralis is a high-performance text-to-speech engine based on **XTTS-v2** and accelerated by **vLLM** (PagedAttention / FlashAttention) with a native **OpenAI-compatible TTS API**:

- **Realtime Factor ≈ 0.02x!** (Synthesizes speech in a fraction of real time)
- **Instant Voice Cloning:** High-fidelity voice cloning from reference audio samples
- **In-Memory Voice Caching:** Speaker embeddings and conditioning latents are cached in RAM for instant voice switching and zero VRAM growth
- **Open WebUI Ready:** Full drop-in compatibility with Open WebUI and any OpenAI TTS client
- **Multi-Request Batching:** Handles concurrent synthesis streams without memory fragmentation

---

## 🐳 Quick Start with Docker Compose

The easiest and most reliable way to run Auralis is with Docker and Docker Compose (CUDA GPU required):

### 1. Clone the repository
```bash
git clone https://github.com/mreschka/Auralis.git
cd Auralis
```

### 2. Add your voice samples
Place your reference audio files (`.wav`) in the `voices/` directory (e.g. `voices/markus.wav`, `voices/marie.wav`).

### 3. Start the container
```bash
docker compose up -d
```

Auralis will start on port `8502` and automatically initialize the XTTS-v2 and vLLM models.

---

## 🔌 Open WebUI Integration

Auralis provides full OpenAI-compatible API endpoints (`/v1/audio/speech`, `/v1/models`, `/v1/audio/voices`).

### Configuration in Open WebUI:

1. Open Open WebUI and go to **Admin Panel ➔ Settings ➔ Audio ➔ TTS Settings**.
2. Configure the following fields:

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **TTS Engine** | `OpenAI` | Standard OpenAI TTS driver |
| **API Base URL** | `http://<your-server-ip>:8502/v1` | Replace with your server IP / hostname |
| **API Key** | `dummy` | Any non-empty string (e.g. `sk-none`) |
| **TTS Model** | `xttsv2` (or `tts-1`) | Exposed via `GET /v1/models` |
| **Default Voice** | `markus` (or any file in `voices/`) | Automatically maps to `voices/<name>.wav` |

3. Save settings. Open WebUI can now synthesize speech and read out assistant responses in real time!

---

## 🎙️ Voice Cloning Guidelines & Best Practices

To get the most natural intonation and highest quality voice clone:

| Parameter | Recommended Value | Notes |
| :--- | :--- | :--- |
| **Format** | **WAV** (`.wav`) | Uncompressed PCM 16-bit |
| **Channels** | **Mono** (1 channel) | Prevents phase distortion |
| **Sample Rate** | **24 000 Hz** (24 kHz) | Native XTTS-v2 sampling rate (16 kHz / 22.05 kHz also supported) |
| **Duration** | **10 to 30 seconds** | ~15–20 seconds of continuous speech is optimal |
| **Acoustics** | **Clean studio recording** | No background music, echo, or room noise |

### Convert audio with FFmpeg:
```bash
ffmpeg -i input.mp3 -af "highpass=f=80, lowpass=f=11000, dynaudnorm" -ar 24000 -ac 1 -c:a pcm_s16le voices/myvoice.wav
```

Any `.wav` file added to `voices/` is immediately available to the API under its filename without requiring a server restart.

---

## ⚡ Performance & Memory Optimizations

This fork includes several critical architectural improvements for 24/7 production environments:

1. **In-Memory Speaker Conditioning Cache:**  
   Speaker embeddings and GPT conditioning latents are hashed (MD5) and cached in RAM upon first use. Consecutive requests and switching between voices skip the expensive mel-spectrogram/perceiver calculation entirely, dropping synthesis latency down to **~2.5–3.5s** per sentence.

2. **Zero-Leak Inference (`torch.set_grad_enabled(False)`):**  
   Autograd graphs are globally disabled during inference, eliminating memory buildup across asynchronous coroutines.

3. **Active CUDA Cache Clearing:**  
   Calls `torch.cuda.empty_cache()` immediately after HiFi-GAN vocoder execution to reclaim transient CUDA memory.

4. **Configurable GPU Memory (`VLLM_GPU_MEMORY_UTILIZATION`):**  
   Allows tuning vLLM's memory budget via environment variable (default `0.45`), enabling smooth co-existence with other LLMs (e.g. Ollama / llama.cpp) on the same GPU.

---

## 🐍 Python Usage

```python
from auralis import TTS, TTSRequest

# Initialize engine
tts = TTS().from_pretrained("AstraMindAI/xttsv2", gpt_model="AstraMindAI/xtts2-gpt")

# Generate speech
request = TTSRequest(
    text="Hallo! Dies ist ein Sprachtest mit Auralis und XTTS-v2.",
    language="de",
    speaker_files=["voices/markus.wav"]
)

output = tts.generate_speech(request)
output.save("output.wav")
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /v1/models` | `GET` | Returns available models (`xttsv2`, `tts-1`, `tts-1-hd`) |
| `GET /v1/audio/voices` | `GET` | Returns list of available voice samples from `voices/` |
| `POST /v1/audio/speech` | `POST` | OpenAI-compatible speech synthesis |

### Example cURL Request:
```bash
curl -X POST http://localhost:8502/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "xttsv2",
    "input": "Hallo Welt, die lokale Sprachsynthese funktioniert einwandfrei!",
    "voice": "markus",
    "response_format": "wav"
  }' \
  --output speech.wav
```

---

## License

This project is licensed under the Apache 2.0 License.
