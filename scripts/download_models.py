"""
Downloads the CLIP ViT-B/32 (LAION-2B) weights used by the zero-shot branch into
models/clip-vit-b32-laion/. The folder is gitignored because the weights are 605 MB.

  python scripts/download_models.py
"""

import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "models" / "clip-vit-b32-laion"
URL = "https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K/resolve/main/"
FILES = ["config.json", "preprocessor_config.json", "tokenizer_config.json", "tokenizer.json",
         "vocab.json", "merges.txt", "special_tokens_map.json", "model.safetensors"]

OUT.mkdir(parents=True, exist_ok=True)
for f in FILES:
    dst = OUT / f
    if dst.exists() and dst.stat().st_size > 0:
        print("have", f)
        continue
    print("downloading", f)
    urllib.request.urlretrieve(URL + f, dst)
print("done:", OUT)
