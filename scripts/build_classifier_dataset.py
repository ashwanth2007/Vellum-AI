"""
Builds the 4-class document-type dataset used by ml/document_classifier.

Classes
  CERTIFICATE      synthetic degree / course / internship certificates + repo certificates
  ACADEMIC_RECORD  synthetic grade sheets, completion / bonafide letters, rendered LORs
  OTHER_DOCUMENT   RVL-CDIP subset (letter class excluded), FUNSD forms, synthetic invoices / menus / articles
  RANDOM_PHOTO     Flickr 1k test photos + Imagenette

Splitting happens on SOURCE items before augmentation, so a phone-photo copy of a
document never lands in a different split from its clean original.

Output
  data/classifier/{train,val,test}/<CLASS>/<id>.jpg
  data/classifier/manifest.csv   (path, label, split, source, variant)
  demo_samples/                  held-out files for the live demo (never used in training)

Usage
  python scripts/build_classifier_dataset.py [--per-class 600]
"""

import argparse
import csv
import io
import random
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))
from synth_documents import (gen_certificate, gen_completion_letter, gen_grade_sheet,  # noqa: E402
                             gen_other_document, phone_photo, render_lor, scan_effect, tint_scan)

CLASSES = ["CERTIFICATE", "ACADEMIC_RECORD", "OTHER_DOCUMENT", "RANDOM_PHOTO"]
OUT = BASE / "data" / "classifier"
DL = OUT / "_downloads"
DEMO = BASE / "demo_samples"
MAX_SIDE = 1100
RVL_NAMES = ["letter", "form", "email", "handwritten", "advertisement", "scientific_report",
             "scientific_publication", "specification", "file_folder", "news_article", "budget",
             "invoice", "presentation", "questionnaire", "resume", "memo"]

_PHOTOS = None  # background photos for phone_photo(), loaded per worker


def _img_from_parquet_cell(cell):
    if isinstance(cell, dict):
        return Image.open(io.BytesIO(cell["bytes"])).convert("RGB")
    return Image.open(io.BytesIO(cell)).convert("RGB")


def load_photo_bytes():
    rows = []
    fl = pd.read_parquet(DL / "flickr1k.parquet")
    col = [c for c in fl.columns if "image" in c.lower()][0]
    rows += [("flickr", r[col]["bytes"] if isinstance(r[col], dict) else r[col]) for _, r in fl.iterrows()]
    inet = DL / "imagenette.parquet"
    if inet.exists():
        im = pd.read_parquet(inet)
        col = [c for c in im.columns if "image" in c.lower()][0]
        rows += [("imagenette", r[col]["bytes"] if isinstance(r[col], dict) else r[col]) for _, r in im.iterrows()]
    return rows


def load_rvl_bytes():
    rows = []
    for f in ["rvl_train.parquet", "rvl_test.parquet"]:
        p = DL / f
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        icol = [c for c in df.columns if "image" in c.lower()][0]
        lcol = [c for c in df.columns if "label" in c.lower()][0]
        for _, r in df.iterrows():
            lab = int(r[lcol])
            if RVL_NAMES[lab] == "letter":
                continue
            rows.append((f"rvl_{RVL_NAMES[lab]}", r[icol]["bytes"] if isinstance(r[icol], dict) else r[icol]))
    return rows


def _init_worker(photo_samples):
    global _PHOTOS
    _PHOTOS = [Image.open(io.BytesIO(b)).convert("RGB").resize((600, 450)) for b in photo_samples]


def _shrink(img):
    img = img.convert("RGB")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    return img


def _render(task):
    """task = (label, source_kind, payload, split, uid, seed). Returns list of manifest rows."""
    label, kind, payload, split, uid, seed = task
    rng = random.Random(seed)
    if kind == "gen_certificate":
        base = gen_certificate(rng)[0]
    elif kind == "gen_grade_sheet":
        base = gen_grade_sheet(rng)[0]
    elif kind == "gen_completion":
        base = gen_completion_letter(rng)[0]
    elif kind == "lor":
        base = render_lor(payload, rng)[0]
    elif kind == "gen_other":
        base = gen_other_document(rng)[0]
    elif kind == "file":
        base = Image.open(payload).convert("RGB")
    else:  # parquet bytes
        base = Image.open(io.BytesIO(payload)).convert("RGB")

    variants = []
    if label == "RANDOM_PHOTO":
        img = base
        if rng.random() < 0.3:  # random crop so framing varies
            w, h = img.size
            cw, ch = int(w * rng.uniform(0.6, 0.95)), int(h * rng.uniform(0.6, 0.95))
            x, y = rng.randint(0, w - cw), rng.randint(0, h - ch)
            img = img.crop((x, y, x + cw, y + ch))
        variants.append(("photo", img))
    else:
        scanned_source = kind.startswith("rvl") or kind == "file" and "funsd" in str(payload).lower()
        if scanned_source:
            doc = tint_scan(base, rng) if rng.random() < 0.5 else base
        else:
            doc = base
        r = rng.random()
        if r < 0.45:
            variants.append(("clean", doc))
        elif r < 0.8:
            variants.append(("phone", phone_photo(doc, rng, _PHOTOS)))
        else:
            variants.append(("scan", scan_effect(doc, rng)))
        # extra phone copy for the classes the demo cares about most
        if label in ("CERTIFICATE", "ACADEMIC_RECORD") and rng.random() < 0.35:
            variants.append(("phone2", phone_photo(doc, rng, _PHOTOS)))

    rows = []
    for vname, img in variants:
        rel = Path(split) / label / f"{uid}_{vname}.jpg"
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        _shrink(img).save(dst, "JPEG", quality=rng.randint(80, 93))
        rows.append({"path": str(rel).replace("\\", "/"), "label": label, "split": split, "source": kind, "variant": vname})
    return rows


def split_of(i, n, rng_split):
    return rng_split.choices(["train", "val", "test"], weights=[0.7, 0.15, 0.15])[0]


def build(per_class: int, workers: int):
    rng = random.Random(2026)
    tasks = []

    def add(label, kind, payload, uid):
        tasks.append((label, kind, payload, rng.choices(["train", "val", "test"], weights=[0.7, 0.15, 0.15])[0],
                      uid, rng.randint(0, 10 ** 9)))

    # CERTIFICATE
    repo_certs = sorted((BASE / "data" / "synthetic" / "certificates").glob("cert_*[0-9].png"))
    for p in repo_certs:
        add("CERTIFICATE", "file", str(p), f"repo_{p.stem}")
    for i in range(max(0, per_class - len(repo_certs))):
        add("CERTIFICATE", "gen_certificate", None, f"gcert_{i:05d}")

    # ACADEMIC_RECORD
    lors = sorted((BASE / "data" / "synthetic" / "lor").glob("lor_*.txt"))
    lors = [p for p in lors if p.stat().st_size > 800]  # skip truncated stubs
    for p in lors:
        add("ACADEMIC_RECORD", "lor", p.read_text(encoding="utf-8"), f"lor_{p.stem}")
    n_letters = int(per_class * 0.17)
    for i in range(n_letters):
        add("ACADEMIC_RECORD", "gen_completion", None, f"letter_{i:05d}")
    for i in range(max(0, per_class - len(lors) - n_letters)):
        add("ACADEMIC_RECORD", "gen_grade_sheet", None, f"grade_{i:05d}")

    # OTHER_DOCUMENT
    rvl = load_rvl_bytes()
    rng.shuffle(rvl)
    funsd = sorted((BASE / "data" / "raw" / "funsd" / "dataset").rglob("*.png"))
    n_syn = int(per_class * 0.2)
    n_funsd = min(len(funsd), int(per_class * 0.2))
    n_rvl = max(0, per_class - n_syn - n_funsd)
    for i, (src, b) in enumerate(rvl[:n_rvl]):
        add("OTHER_DOCUMENT", src, b, f"{src}_{i:05d}")
    for p in funsd[:n_funsd]:
        add("OTHER_DOCUMENT", "file", str(p), f"funsd_{p.stem}")
    for i in range(n_syn):
        add("OTHER_DOCUMENT", "gen_other", None, f"gother_{i:05d}")

    # RANDOM_PHOTO
    photos = load_photo_bytes()
    rng.shuffle(photos)
    for i, (src, b) in enumerate(photos[:per_class]):
        add("RANDOM_PHOTO", src, b, f"{src}_{i:05d}")
    bg_samples = [b for _, b in photos[per_class:per_class + 60]] or [b for _, b in photos[:60]]

    print(f"[*] {len(tasks)} source items, rendering with {workers} workers ...", flush=True)
    rows = []
    with Pool(workers, initializer=_init_worker, initargs=(bg_samples,)) as pool:
        for k, r in enumerate(pool.imap_unordered(_render, tasks, chunksize=8)):
            rows += r
            if (k + 1) % 250 == 0:
                print(f"    {k + 1}/{len(tasks)}", flush=True)

    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "label", "split", "source", "variant"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda x: x["path"]))
    df = pd.DataFrame(rows)
    print(df.groupby(["split", "label"]).size().unstack(fill_value=0))
    return photos[per_class + 60:]


def build_demo(spare_photos):
    """Held-out demo files, generated from fresh seeds and never seen in training."""
    DEMO.mkdir(exist_ok=True)
    rng = random.Random(777)
    _init_worker([b for _, b in spare_photos[:20]] if spare_photos else [])
    c1 = gen_certificate(rng)[0]
    c1.save(DEMO / "01_certificate_course_completion.png")
    c2 = gen_certificate(random.Random(91))[0]
    c2.save(DEMO / "02_certificate_degree.pdf", "PDF", resolution=150)
    g1 = gen_grade_sheet(random.Random(5))[0]
    phone_photo(g1, random.Random(8), _PHOTOS).save(DEMO / "03_grade_sheet_phone_photo.jpg", quality=88)
    g2 = gen_grade_sheet(random.Random(42))[0]
    l2 = gen_completion_letter(random.Random(43))[0]
    g2.save(DEMO / "04_transcript_two_pages.pdf", "PDF", resolution=150, save_all=True, append_images=[l2])
    o1 = gen_other_document(random.Random(12))[0]
    o1.save(DEMO / "05_other_invoice.png")
    rvl = load_rvl_bytes()
    Image.open(io.BytesIO(rvl[-1][1])).convert("RGB").save(DEMO / "06_other_scanned_form.jpg", quality=90)
    if spare_photos:
        for i, (src, b) in enumerate(spare_photos[-2:]):
            Image.open(io.BytesIO(b)).convert("RGB").save(DEMO / f"0{7 + i}_random_photo.jpg", quality=90)
    (DEMO / "09_not_supported.txt").write_text("Plain text file, the API should reject this with a clear message.\n")
    print(f"[OK] demo samples written to {DEMO}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=600)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    spare = build(a.per_class, a.workers)
    build_demo(spare)
