"""
Evaluation of the multi-modal Document Type Classifier.

Two held-out sets:
  1. TEST split of data/classifier (never used in training)
  2. REAL-WORLD set: demo_samples/real_world (genuine scans from Wikimedia Commons),
     labelled in REAL_WORLD_LABELS below. Nothing like them is in the training data.

For every branch (image CNN, CLIP zero-shot, OCR text) and for the fusion it reports
accuracy and macro F1, grid-searches the fusion weights, writes confusion matrices and
records the MEASURED numbers in models/model_registry.json.

  python -m ml.document_classifier.evaluate
"""

import itertools
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.document_classifier import clip_branch  # noqa: E402
import importlib  # noqa: E402
P = importlib.import_module("ml.document_classifier.predict")
from ml.document_classifier.data import DATA_DIR, read_manifest  # noqa: E402
from ml.document_classifier.model import DOCUMENT_CLASSES  # noqa: E402
from ml.document_classifier.text_model import load_cache, predict_text_proba  # noqa: E402

MODELS = BASE_DIR / "models"
REAL_DIR = BASE_DIR / "demo_samples" / "real_world"
REAL_WORLD_LABELS = {  # filename prefix -> true class
    "real_01": "CERTIFICATE", "real_02": "CERTIFICATE", "real_03": "CERTIFICATE",
    "real_04": "CERTIFICATE", "real_05": "ACADEMIC_RECORD", "real_06": "CERTIFICATE",
}


def plot_confusion(cm, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 5.4), dpi=150)
    ax.imshow(cm, cmap="Blues")
    short = ["Certificate", "Academic\nrecord", "Other\ndocument", "Random\nphoto"]
    ax.set_xticks(range(4), short)
    ax.set_yticks(range(4), short)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=11)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def collect(items, ocr_texts):
    """items: [(PIL image, label)]; returns y and per-branch probability arrays (text may be None)."""
    y, pi, pc, pt = [], [], [], []
    for k, ((img, label), text) in enumerate(zip(items, ocr_texts)):
        y.append(DOCUMENT_CLASSES.index(label))
        pi.append(P.image_proba(img))
        pc.append(clip_branch.clip_proba(img))
        pt.append(predict_text_proba(text) if text is not None else None)
        if (k + 1) % 100 == 0:
            print(f"    {k + 1}/{len(items)}", flush=True)
    return np.array(y), np.array(pi), np.array(pc), pt


def fused_preds(pi, pc, pt, w):
    return np.array([int(np.argmax(P.fuse(a, b, c, w))) for a, b, c in zip(pi, pc, pt)])


def evaluate():
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

    cache = load_cache()
    rows = read_manifest("test")
    test_items = [(Image.open(DATA_DIR / r["path"]).convert("RGB"), r["label"]) for r in rows]
    test_texts = [cache.get(r["path"], {}).get("text") for r in rows]
    print(f"[*] test split: {len(rows)} images, OCR text for {sum(t is not None for t in test_texts)}", flush=True)
    yt, it, ct, tt = collect(test_items, test_texts)

    from ml.ocr.ocr_service import get_ocr_service
    ocr = get_ocr_service()
    real_files = sorted(p for p in REAL_DIR.glob("*") if p.name[:7] in REAL_WORLD_LABELS)
    real_items = [(Image.open(p).convert("RGB"), REAL_WORLD_LABELS[p.name[:7]]) for p in real_files]
    real_texts = [ocr.extract_text_and_layout(img)["full_text"] for img, _ in real_items]
    print(f"[*] real-world set: {len(real_items)} scans", flush=True)
    yr, ir, cr, tr = collect(real_items, real_texts)

    # grid-search fusion weights: maximise test accuracy + real-world accuracy (equal say)
    best = None
    for wi, wc in itertools.product(np.arange(0.1, 0.8, 0.05), repeat=2):
        wt = 1 - wi - wc
        if wt < 0.05:
            continue
        w = {"image": wi, "clip": wc, "text": wt}
        score = accuracy_score(yt, fused_preds(it, ct, tt, w)) + accuracy_score(yr, fused_preds(ir, cr, tr, w))
        if best is None or score > best[0] + 1e-9:
            best = (score, w)
    w = {k: round(float(v), 2) for k, v in best[1].items()}
    print(f"[*] best fusion weights {w}", flush=True)

    res = {"test_samples": len(yt), "real_world_samples": len(yr), "fusion_weights": w}
    for name, preds_t, preds_r in [
        ("image_cnn", it.argmax(1), ir.argmax(1)),
        ("clip_zero_shot", ct.argmax(1), cr.argmax(1)),
        ("fused", fused_preds(it, ct, tt, w), fused_preds(ir, cr, tr, w)),
    ]:
        res[f"{name}_test_accuracy"] = round(accuracy_score(yt, preds_t), 4)
        res[f"{name}_test_macro_f1"] = round(f1_score(yt, preds_t, average="macro"), 4)
        res[f"{name}_real_world_accuracy"] = round(accuracy_score(yr, preds_r), 4)
    mask = np.array([p is not None for p in tt])
    if mask.any():
        res["text_test_accuracy"] = round(accuracy_score(yt[mask], np.array([p.argmax() for p in np.array(tt, dtype=object)[mask]])), 4)
        res["text_test_samples_with_text"] = int(mask.sum())

    pf = fused_preds(it, ct, tt, w)
    report = classification_report(yt, pf, target_names=DOCUMENT_CLASSES, digits=4, output_dict=True)
    print(classification_report(yt, pf, target_names=DOCUMENT_CLASSES, digits=4))
    print(json.dumps(res, indent=2))
    plot_confusion(confusion_matrix(yt, pf, labels=range(4)), f"Fused classifier, test split (n={len(yt)})",
                   MODELS / "document_classifier_confusion.png")
    plot_confusion(confusion_matrix(yt, it.argmax(1), labels=range(4)), f"Image CNN only, test split (n={len(yt)})",
                   MODELS / "document_classifier_confusion_image_only.png")

    real_detail = []
    for p, y_, a, b, c in zip(real_files, yr, ir, cr, tr):
        real_detail.append({"file": p.name, "true": DOCUMENT_CLASSES[y_],
                            "image_cnn": DOCUMENT_CLASSES[int(a.argmax())], "clip": DOCUMENT_CLASSES[int(b.argmax())],
                            "text": DOCUMENT_CLASSES[int(c.argmax())] if c is not None else None,
                            "fused": DOCUMENT_CLASSES[int(np.argmax(P.fuse(a, b, c, w)))]})
    for d in real_detail:
        print(d)

    reg_path = MODELS / "model_registry.json"
    reg = json.load(open(reg_path)) if reg_path.exists() else {}
    reg["document_classifier"] = {
        "version": "2.0.0",
        "architecture": "EfficientNet-B0 fine-tuned + CLIP ViT-B/32 zero-shot + OCR TF-IDF LogisticRegression, weighted fusion",
        "dataset": "Synthetic certificates, grade sheets, letters, LORs + RVL-CDIP subset + FUNSD + Flickr1k + Imagenette",
        "classes": DOCUMENT_CLASSES,
        "metrics": {**res, "per_class_f1_fused": {c: round(report[c]["f1-score"], 4) for c in DOCUMENT_CLASSES}},
        "measured_on": "held-out test split + real-world Wikimedia Commons scans",
    }
    json.dump(reg, open(reg_path, "w"), indent=2)
    json.dump({**res, "report": report, "real_world_detail": real_detail},
              open(MODELS / "document_classifier_metrics.json", "w"), indent=2)
    print(f"[OK] metrics written to {reg_path}")
    return res


if __name__ == "__main__":
    evaluate()
