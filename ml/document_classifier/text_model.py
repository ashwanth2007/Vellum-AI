"""
Text branch of the document classifier.

OCR text of every image (RapidOCR) -> TF-IDF (word 1-2 grams + char 3-5 grams)
-> multinomial logistic regression over the same 4 classes.

  python -m ml.document_classifier.text_model ocr     # OCR the dataset into data/classifier/ocr_cache.jsonl
  python -m ml.document_classifier.text_model train   # fit + save models/document_text_model.joblib

The OCR step caches results, so it can be stopped and resumed.
"""

import json
import sys
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import csv  # noqa: E402

DOCUMENT_CLASSES = ["CERTIFICATE", "ACADEMIC_RECORD", "OTHER_DOCUMENT", "RANDOM_PHOTO"]
DATA_DIR = BASE_DIR / "data" / "classifier"


def read_manifest(split: str):
    with open(DATA_DIR / "manifest.csv", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["split"] == split]

CACHE = DATA_DIR / "ocr_cache.jsonl"
MODEL_PATH = BASE_DIR / "models" / "document_text_model.joblib"
MIN_WORDS = 5
_model = None


def load_cache():
    out = {}
    for fp in sorted(DATA_DIR.glob("ocr_cache*.jsonl")):
        for line in open(fp, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # a shard killed mid-write leaves a partial last line
            out[r["path"]] = r
    return out


def run_ocr(train_per_class: int = 300, shard: int = 0, nshards: int = 1):
    """OCR the whole val + test split and up to train_per_class train images per class."""
    from ml.ocr.ocr_service import get_ocr_service
    ocr = get_ocr_service()
    print(f"[*] OCR engine: {ocr.engine_name}", flush=True)
    done = load_cache()
    todo = []
    for split in ("test",):
        todo += read_manifest(split)
    rng = np.random.default_rng(0)
    train = read_manifest("train")
    for c in DOCUMENT_CLASSES:
        rows = [r for r in train if r["label"] == c]
        idx = rng.permutation(len(rows))[:train_per_class]
        todo += [rows[i] for i in idx]
    todo = [r for r in todo if r["path"] not in done][shard::nshards]
    print(f"[*] shard {shard}/{nshards}: {len(done)} cached, {len(todo)} to OCR", flush=True)
    with open(DATA_DIR / f"ocr_cache_{shard}.jsonl", "a", encoding="utf-8") as f:
        for k, r in enumerate(todo):
            res = ocr.extract_text_and_layout(DATA_DIR / r["path"])
            f.write(json.dumps({"path": r["path"], "label": r["label"], "split": r["split"],
                                "text": res["full_text"], "words": res["word_count"]}) + "\n")
            if (k + 1) % 50 == 0:
                f.flush()
                print(f"    {k + 1}/{len(todo)}", flush=True)


def build_pipeline():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline
    feats = FeatureUnion([
        ("word", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=40000)),
        ("char", TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True, max_features=60000)),
    ])
    return Pipeline([("tfidf", feats), ("clf", LogisticRegression(C=4.0, max_iter=3000, class_weight="balanced"))])


def train():
    import joblib
    from sklearn.metrics import accuracy_score, classification_report
    cache = load_cache()
    rows = list(cache.values())
    tr = [r for r in rows if r["split"] == "train"]
    te = [r for r in rows if r["split"] == "test"]
    print(f"[*] text train {len(tr)} | test {len(te)}", flush=True)
    pipe = build_pipeline()
    pipe.fit([r["text"] for r in tr], [r["label"] for r in tr])
    pred = pipe.predict([r["text"] for r in te])
    acc = accuracy_score([r["label"] for r in te], pred)
    print(classification_report([r["label"] for r in te], pred, digits=4))
    joblib.dump(pipe, MODEL_PATH)
    print(f"[OK] text model test accuracy {acc:.4f}, saved {MODEL_PATH}", flush=True)
    return acc


def get_text_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        import joblib
        # joblib unpickles: only ever load the model this repo trained itself, never a downloaded file
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_text_proba(text: str):
    """Return a probability vector in DOCUMENT_CLASSES order, or None if no model or too little text."""
    m = get_text_model()
    if m is None or len(text.split()) < MIN_WORDS:
        return None
    p = m.predict_proba([text])[0]
    order = list(m.classes_)
    return np.array([p[order.index(c)] for c in DOCUMENT_CLASSES])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "train"
    if cmd == "ocr":
        a = [int(x) for x in sys.argv[2:]]
        run_ocr(*(a or [300]))
    else:
        train()
