# Voice Reference Samples

Place your `.wav` reference voice samples in this directory. Any file placed here is automatically discovered and can be selected by its basename (e.g. `voice: "markus"` for `markus.wav`).

---

## 🎙️ Optimal Voice Sample Guidelines

For the highest quality voice cloning and natural intonation with XTTS-v2:

| Parameter | Recommended Value | Notes |
| :--- | :--- | :--- |
| **File Format** | **WAV** (`.wav`) | Uncompressed PCM 16-bit |
| **Channels** | **Mono** (1 channel) | Avoid stereo recordings to prevent phase issues |
| **Sample Rate** | **24 000 Hz** (24 kHz) or **22 050 Hz** / **16 000 Hz** | Native XTTS sampling rate is 24 kHz |
| **Duration** | **10 to 30 seconds** | Ideal length is ~15-20 seconds of continuous speech |
| **Audio Quality** | **Studio clean** | No background music, no reverb/echo, no background noise |
| **Content** | Diverse phonetic sentences | Natural spoken tempo, clear pronunciation |

---

## ✂️ Preparing Audio with FFmpeg

You can convert any existing audio or video recording into the optimal format using `ffmpeg`:

```bash
# Convert, resample to 24kHz mono 16-bit PCM, and normalize volume
ffmpeg -i input.mp3 -af "highpass=f=80, lowpass=f=11000, dynaudnorm" -ar 24000 -ac 1 -c:a pcm_s16le markus.wav
```
