"""
Zero-shot CLIP branch of the document classifier.

CLIP ViT-B/32 (LAION-2B weights, models/clip-vit-b32-laion) scores the image against a
set of natural-language descriptions per class. It was trained on ~2 billion real
image-text pairs and has never seen our synthetic training data, so it covers the
real-world scans (old diplomas, foreign-language certificates, handwritten record books)
where the fine-tuned CNN is weakest.

  python -m ml.document_classifier.clip_branch <image>
"""

import sys
from pathlib import Path

import numpy as np
import torch

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLIP_DIR = BASE_DIR / "models" / "clip-vit-b32-laion"
DOCUMENT_CLASSES = ["CERTIFICATE", "ACADEMIC_RECORD", "OTHER_DOCUMENT", "RANDOM_PHOTO"]

PROMPTS = {
    "CERTIFICATE": [
        "a scan of a university degree certificate",
        "a photo of a diploma",
        "a certificate of completion with a signature and a seal",
        "an award certificate with a decorative border",
        "an academic diploma written in latin or another language",
        "a framed graduation diploma",
        "a course completion certificate",
    ],
    "ACADEMIC_RECORD": [
        "a university grade sheet with a table of courses and grades",
        "a student mark sheet with subjects and marks",
        "an academic transcript of records",
        "a report card with grades",
        "a student record book with handwritten grades",
        "a letter of recommendation from a professor on university letterhead",
        "a letter from a university registrar",
    ],
    "OTHER_DOCUMENT": [
        "a scanned invoice or receipt",
        "a filled in paper form",
        "a newspaper page",
        "a business memo or email printout",
        "a bank statement",
        "a restaurant menu",
        "a page of a scientific paper",
        "an advertisement flyer",
    ],
    "RANDOM_PHOTO": [
        "a photo of a person",
        "a photo of an animal",
        "a photo of a landscape",
        "a photo of a street or a city",
        "a photo of food",
        "a photo of an object",
        "a selfie",
        "a photo of a vehicle",
    ],
}

_state = {}


def _load():
    if "model" not in _state:
        from transformers import CLIPModel, CLIPProcessor
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = CLIPModel.from_pretrained(str(CLIP_DIR), use_safetensors=True).to(dev).eval()
        proc = CLIPProcessor.from_pretrained(str(CLIP_DIR))
        texts, owner = [], []
        for i, c in enumerate(DOCUMENT_CLASSES):
            texts += PROMPTS[c]
            owner += [i] * len(PROMPTS[c])
        with torch.no_grad():
            t = proc(text=texts, return_tensors="pt", padding=True).to(dev)
            tf = model.text_projection(model.text_model(input_ids=t["input_ids"], attention_mask=t["attention_mask"]).pooler_output)
            tf = tf / tf.norm(dim=-1, keepdim=True)
        # one mean text embedding per class (prompt ensembling)
        owner = torch.tensor(owner, device=dev)
        cls_emb = torch.stack([tf[owner == i].mean(0) for i in range(len(DOCUMENT_CLASSES))])
        cls_emb = cls_emb / cls_emb.norm(dim=-1, keepdim=True)
        _state.update(model=model, proc=proc, cls=cls_emb, dev=dev)
    return _state


def available() -> bool:
    return (CLIP_DIR / "model.safetensors").exists()


def clip_proba(pil_image) -> np.ndarray:
    s = _load()
    with torch.no_grad():
        x = s["proc"](images=pil_image.convert("RGB"), return_tensors="pt").to(s["dev"])
        f = s["model"].visual_projection(s["model"].vision_model(pixel_values=x["pixel_values"]).pooler_output)
        f = f / f.norm(dim=-1, keepdim=True)
        logits = 100.0 * f @ s["cls"].T
        return torch.softmax(logits, dim=-1).squeeze(0).float().cpu().numpy()


if __name__ == "__main__":
    from PIL import Image
    for p in sys.argv[1:]:
        pr = clip_proba(Image.open(p))
        print(Path(p).name, DOCUMENT_CLASSES[int(pr.argmax())], np.round(pr, 3))
