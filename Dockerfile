FROM python:3.10-slim

WORKDIR /app

# System dependencies for audio processing and build tools
RUN apt-get update && apt-get install -y --no-install-recommends     ffmpeg     libsndfile1     build-essential     portaudio19-dev     git     pkg-config     && rm -rf /var/lib/apt/lists/*

# PyTorch & Torchaudio with CUDA 12.1 support
RUN pip install --no-cache-dir --upgrade pip &&     pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install local package and pin transformers 4.45.2
COPY setup.py requirements.txt README.md /app/
COPY src /app/src
RUN pip install --no-cache-dir -e /app &&     pip install --no-cache-dir transformers==4.45.2

EXPOSE 8502

ENTRYPOINT [ "auralis.openai" ]

CMD [     "--host", "0.0.0.0",     "--port", "8502",     "--model", "AstraMindAI/xttsv2",     "--gpt_model", "AstraMindAI/xtts2-gpt",     "--max_concurrency", "4" ]
