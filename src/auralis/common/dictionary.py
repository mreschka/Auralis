"""Phonetic dictionary and custom pronunciation registry for Auralis TTS Normalizer.

This module provides phonetic overrides for acronyms, technical terms, developer tools,
and brand names to ensure natural and correct pronunciation in speech synthesis.
Users can extend this by editing this file or placing a 'pronunciations.json' file in the app directory.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional

# Default technical & developer term pronunciations
DEFAULT_PRONUNCIATIONS: Dict[str, str] = {
    # Java & Runtime Environments
    "jdk": "J-D-K",
    "jre": "J-R-E",
    "jvm": "J-V-M",
    "jar": "Dschahr",
    "openjdk": "Open J-D-K",
    "adoptium": "Adoptium",
    "temurin": "Temurin",
    "gradle": "Greidel",
    "maven": "Meiwen",

    # Web & Protocols
    "api": "A-P-I",
    "apis": "A-P-Is",
    "rest": "Rest",
    "http": "H-T-T-P",
    "https": "H-T-T-P-S",
    "url": "U-R-L",
    "urls": "U-R-Ls",
    "uri": "U-R-I",
    "ip": "I-P",
    "ipv4": "I-P-v-4",
    "ipv6": "I-P-v-6",
    "ssh": "S-S-H",
    "ssl": "S-S-L",
    "tls": "T-L-S",
    "ftp": "F-T-P",
    "dns": "D-N-S",
    "dhcp": "D-H-C-P",

    # Formats & Languages
    "json": "Jeyson",
    "yaml": "Jammel",
    "yml": "Jammel",
    "sql": "S-Q-L",
    "nosql": "No-S-Q-L",
    "html": "H-T-M-L",
    "css": "C-S-S",
    "xml": "X-M-L",
    "csv": "C-S-V",
    "regex": "Reg-Ex",
    "jwt": "Jot-We-Te",

    # Interfaces & Frameworks
    "gui": "G-U-I",
    "ui": "U-I",
    "cli": "C-L-I",
    "sdk": "S-D-K",
    "ide": "I-D-E",
    "webui": "Web U-I",
    "openwebui": "Open Web U-I",

    # DevOps & Infrastructure
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "nginx": "Engine X",
    "docker": "Docker",
    "github": "Git-Hub",
    "gitlab": "Git-Lab",
    "ci/cd": "C-I C-D",

    # AI & Compute
    "tts": "T-T-S",
    "ttft": "T-T-F-T",
    "llm": "L-L-M",
    "llms": "L-L-Ms",
    "vllm": "v-L-L-M",
    "ollama": "O-Llama",
    "gpu": "G-P-U",
    "gpus": "G-P-Us",
    "cpu": "C-P-U",
    "cpus": "C-P-Us",
    "ram": "Ram",
    "vram": "V-Ram",
    "ssd": "S-S-D",
    "nvme": "N-V-M-e",
    "os": "O-S",
}


def load_pronunciations(custom_file: Optional[str] = None) -> Dict[str, str]:
    """Load default pronunciations merged with any user-provided custom JSON file."""
    pronunciations = dict(DEFAULT_PRONUNCIATIONS)

    # Search standard paths for custom pronunciations.json
    candidates = [
        custom_file,
        os.getenv("AURALIS_PRONUNCIATION_FILE"),
        "/app/data/pronunciations.json",
        "/app/pronunciations.json",
        "data/pronunciations.json",
        "pronunciations.json",
    ]

    for path_str in candidates:
        if not path_str:
            continue
        p = Path(path_str)
        if p.exists() and p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    user_dict = json.load(f)
                    if isinstance(user_dict, dict):
                        pronunciations.update(user_dict)
                        break
            except Exception:
                pass

    return pronunciations
