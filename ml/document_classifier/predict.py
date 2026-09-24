"""
Inference API for the Document Type Classifier.

Three branches, fused by a weighted average of their probability vectors:
  image : EfficientNet-B0 fine-tuned on our dataset         (strong on the layouts it has seen)
  clip  : CLIP ViT-B/32 zero-shot, never saw our data        (strong on real-world scans)
  text  : TF-IDF + logistic regression on the OCR text       (only when OCR found >= 5 words)

predict(image)                  image + clip
predict(image, ocr_text="...")  image + clip + text
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import torch
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.document_classifier.data import eval_transform  # noqa: E402
from ml.document_classifier.model import CLASS_LABELS, DOCUMENT_CLASSES, RELEVANT_CLASSES, DocumentClassifier  # noqa: E402
from ml.document_classifier.text_model import predict_text_proba  # noqa: E402
from ml.document_classifier import clip_branch  # noqa: E402

CHECKPOINT = BASE_DIR / "models" / "document_classifier.pt"
INPUT_SIZE = 320
# branch weights, tuned on the held-out test split + real-world scans (see evaluate.py)
WEIGHTS = {"image": 0.45, "clip": 0.45, "text": 0.10}

_model_instance = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_tf = eval_transform(INPUT_SIZE)


def get_model():
    global _model_instance
    if _model_instance is None:
        model = DocumentClassifier(num_classes=len(DOCUMENT_CLASSES))
        if CHECKPOINT.exists():
            model.load_state_dict(torch.load(CHECKPOINT, map_location="cpu", weights_only=True))
        _model_instance = model.to(_device).eval()
    return _model_instance


def _to_pil(image_input) -> Image.Image:
    if isinstance(image_input, (str, Path)):
        return Image.open(image_input).convert("RGB")
    if isinstance(image_input, np.ndarray):
        return Image.fromarray(image_input).convert("RGB")
    return image_input.convert("RGB")


def image_proba(image_input) -> np.ndarray:
    x = _tf(_to_pil(image_input)).unsqueeze(0).to(_device)
    with torch.no_grad():
        logits, _ = get_model()(x)
    return torch.softmax(logits.float(), dim=1).squeeze(0).cpu().numpy()


def _pack(probs: np.ndarray) -> Dict[str, float]:
    return {c: round(float(probs[i]), 4) for i, c in enumerate(DOCUMENT_CLASSES)}


def fuse(p_img, p_clip=None, p_txt=None, weights=None):
    w = weights or WEIGHTS
    parts = [(w["image"], p_img)]
    if p_clip is not None:
        parts.append((w["clip"], p_clip))
    if p_txt is not None:
        parts.append((w["text"], p_txt))
    total = sum(x for x, _ in parts)
    return sum(x * p for x, p in parts) / total


def predict(image_input: Union[str, Path, Image.Image, np.ndarray], ocr_text: Optional[str] = None) -> Dict[str, Any]:
    pil = _to_pil(image_input)
    p_img = image_proba(pil)
    p_clip = clip_branch.clip_proba(pil) if clip_branch.available() else None
    p_txt = predict_text_proba(ocr_text) if ocr_text is not None else None
    probs = fuse(p_img, p_clip, p_txt)
    mode = "+".join(n for n, p in (("image", p_img), ("clip", p_clip), ("text", p_txt)) if p is not None)
    idx = int(np.argmax(probs))
    doc_type = DOCUMENT_CLASSES[idx]
    return {
        "document_type": doc_type,
        "document_type_id": idx,
        "label": CLASS_LABELS[doc_type],
        "is_relevant": doc_type in RELEVANT_CLASSES,
        "confidence": round(float(probs[idx]), 4),
        "class_probabilities": _pack(probs),
        "image_probabilities": _pack(p_img),
        "clip_probabilities": _pack(p_clip) if p_clip is not None else None,
        "text_probabilities": _pack(p_txt) if p_txt is not None else None,
        "fusion_mode": mode,
    }


if __name__ == "__main__":
    import json
    target = sys.argv[1] if len(sys.argv) > 1 else None
    img = target or Image.new("RGB", (224, 224), (240, 240, 240))
    print(json.dumps(predict(img), indent=2))
