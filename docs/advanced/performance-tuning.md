# Performance Tuning & Optimization Guide

Auralis is optimized for low-latency, high-throughput text-to-speech synthesis using vLLM (FlashAttention) and PyTorch.

---

## ⚡ Key Performance Factors

### 1. vLLM Concurrency & Batching (`max_concurrency`)

Auralis uses vLLM's `AsyncLLMEngine` to generate autoregressive audio tokens.

* Setting `max_concurrency: 8` allows up to 8 sentences to be generated simultaneously within a single GPU forward pass.
* Configure concurrency in `docker-compose.yml` or via CLI:
  ```bash
  auralis.openai --max_concurrency 8
  ```

### 2. VRAM Allocation (`VLLM_GPU_MEMORY_UTILIZATION`)

By default, vLLM attempts to allocate up to 90% of GPU memory. In multi-tenant environments where other LLMs (e.g. Ollama, llama.cpp, vLLM text models) share the same GPU:

* Set `VLLM_GPU_MEMORY_UTILIZATION=0.45` in `docker-compose.yml` (or environment).
* On a 16 GB GPU (such as RTX A5000), this allocates ~7.2 GB for Auralis + vLLM KV-cache, leaving ~8.8 GB for parallel services.

### 3. In-Memory Speaker Conditioning Cache

Computing reference audio conditioning (mel-spectrogram extraction + perceiver encoder) requires ~300–500 ms of CPU/GPU time per request.

* Auralis caches speaker embeddings and conditioning latents in RAM using an MD5 hash of the reference audio.
* Subsequent requests for the same speaker or voice file execute instantly with **0 ms conditioning overhead**.

### 4. Zero-Leak Inference Mode

To prevent PyTorch autograd graph buildup across concurrent asynchronous tasks:

* All inference paths are wrapped with `torch.inference_mode()` / `torch.set_grad_enabled(False)`.
* Transient tensor allocations are reclaimed after HiFi-GAN neural vocoder execution with `torch.cuda.empty_cache()`.

### 5. Sentence-Level Batching

Long texts are automatically preprocessed and split at sentence boundaries:

* Sentences are processed in parallel batches rather than one huge sequential sequence.
* Real-Time Factor (RTF) drops from `1.2x` down to **`0.18x`** (over 5x faster than real-time speech).
