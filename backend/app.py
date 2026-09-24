"""
FastAPI REST API Server for Vellum Document Verification Platform.
Exposes modular endpoints for document classification, OCR, entity extraction,
forensic tampering localization, signature & stamp verification, LOR NLP analysis,
cross-document verification, and evidence fusion.
"""

import os
import sys
import io
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import numpy as np
import uvicorn

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.ocr.ocr_service import get_ocr_service
from ml.nlp.entity_extractor import EntityExtractor
from ml.nlp.lor_analyzer import LORAnalyzer
import ml.document_classifier as doc_module
import ml.tampering as tamper_module
import ml.signature as sig_module
import ml.stamp as stamp_module
from ml.cross_verification.cross_verifier import CrossDocumentVerifier
from ml.fusion.evidence_fusion import fuse
from ml.utils.hardware import detect_hardware
from ml.nlp.field_extractor import FieldExtractor

app = FastAPI(
    title="Vellum Verification API",
    description="Multi-Modal AI Document Verification & Cross-Document Forensics Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ocr_service = get_ocr_service()
entity_extractor = EntityExtractor()
lor_analyzer = LORAnalyzer()
cross_verifier = CrossDocumentVerifier()
field_extractor = FieldExtractor()


@app.get("/api/health")
def health_check():
    hw = detect_hardware()
    registry_path = BASE_DIR / "models" / "model_registry.json"
    registry = {}
    if registry_path.exists():
        with open(registry_path, "r") as f:
            registry = json.load(f)

    return {
        "status": "HEALTHY",
        "service": "Vellum Document Verification Engine",
        "version": "1.0.0",
        "hardware": hw,
        "models_loaded": list(registry.keys())
    }


@app.get("/api/models/registry")
def get_model_registry():
    registry_path = BASE_DIR / "models" / "model_registry.json"
    if not registry_path.exists():
        raise HTTPException(status_code=404, detail="Model registry not initialized.")
    with open(registry_path, "r") as f:
        return json.load(f)


@app.post("/api/verify/single-document")
async def verify_single_document(
    file: UploadFile = File(...),
    reference_signature: Optional[UploadFile] = File(None),
    reference_stamp: Optional[UploadFile] = File(None)
):
    """
    Complete single document verification pipeline:
    Classification -> OCR -> Entity Extraction -> Tampering Forensics -> Signature -> Stamp -> Evidence Fusion.
    """
    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(pil_img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    # 1. Document Classifier
    cls_res = doc_module.predict(img_np)
    doc_type = cls_res["document_type"]

    # 2. OCR Service
    ocr_res = ocr_service.extract_text_and_layout(img_np)

    # 3. Entity Extraction
    extracted_entities = entity_extractor.extract_from_text_and_layout(ocr_res["full_text"], ocr_res["lines"])

    # 4. Tampering Forensics
    tamper_res = tamper_module.predict(img_np)

    # 5. Signature Verification
    ref_sig_img = None
    if reference_signature:
        ref_sig_bytes = await reference_signature.read()
        ref_sig_img = Image.open(io.BytesIO(ref_sig_bytes)).convert("L")
    sig_res = sig_module.predict(img_np, reference_signature=ref_sig_img)

    # 6. Stamp Verification
    ref_stamp_img = None
    if reference_stamp:
        ref_stamp_bytes = await reference_stamp.read()
        ref_stamp_img = Image.open(io.BytesIO(ref_stamp_bytes)).convert("RGB")
    stamp_res = stamp_module.predict(img_np, reference_stamp=ref_stamp_img)

    # 7. Evidence Fusion
    fusion_signals = {
        "tampering_probability": tamper_res["tampering_probability"],
        "signature_similarity": sig_res["similarity_score"] if sig_res["reference_available"] else None,
        "stamp_present": stamp_res["stamp_present"],
        "ocr_confidence": ocr_res["average_confidence"],
        "issuer_match": bool(extracted_entities.get("institution")),
        "qr_match": True
    }
    fusion_res = fuse(fusion_signals)

    return {
        "document_name": file.filename,
        "classification": cls_res,
        "ocr": {
            "full_text": ocr_res["full_text"][:500],
            "line_count": len(ocr_res["lines"]),
            "average_confidence": ocr_res["average_confidence"],
            "engine": ocr_res["engine"]
        },
        "extracted_entities": extracted_entities,
        "tampering_analysis": {
            "status": tamper_res["status"],
            "is_tampered": tamper_res["is_tampered"],
            "tampering_probability": tamper_res["tampering_probability"],
            "suspicious_regions_count": tamper_res["suspicious_regions_count"],
            "field_explanations": tamper_res["field_explanations"],
            "suspicious_bboxes": tamper_res["suspicious_bboxes"]
        },
        "signature_verification": sig_res,
        "stamp_verification": stamp_res,
        "evidence_fusion": fusion_res
    }


# ---------------------------------------------------------------------------------------------
# /api/analyze : the prototype pipeline (any upload -> type check -> classification -> fields)
# ---------------------------------------------------------------------------------------------
import base64
import time

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 5
PDF_DPI = 300
PREVIEW_MAX_SIDE = 1400
IMAGE_FORMATS = {"PNG", "JPEG", "WEBP", "BMP", "TIFF", "GIF", "MPO"}


def _load_pages(data: bytes):
    """Return (mime, total_pages, [PIL pages]). Raises HTTPException(415) for unsupported files."""
    if data[:5] == b"%PDF-":
        import fitz  # PyMuPDF
        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as e:
            raise HTTPException(status_code=415, detail=f"This PDF could not be opened: {e}")
        pages = []
        for i in range(min(len(doc), MAX_PDF_PAGES)):
            pix = doc[i].get_pixmap(dpi=PDF_DPI, alpha=False)
            pages.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        if not pages:
            raise HTTPException(status_code=415, detail="This PDF has no pages.")
        return "application/pdf", len(doc), pages
    try:
        img = Image.open(io.BytesIO(data))
        fmt = (img.format or "").upper()
        img.load()
    except Exception:
        raise HTTPException(status_code=415, detail="Unsupported file. Upload an image (PNG, JPG, WEBP, BMP, TIFF) or a PDF.")
    if fmt not in IMAGE_FORMATS:
        raise HTTPException(status_code=415, detail=f"Unsupported image format '{fmt}'. Upload PNG, JPG, WEBP, BMP, TIFF or PDF.")
    from PIL import ImageOps
    img = ImageOps.exif_transpose(img).convert("RGB")  # phone photos carry EXIF rotation
    return f"image/{'jpeg' if fmt == 'MPO' else fmt.lower()}", 1, [img]


def _preview(img: Image.Image, lines):
    s = min(1.0, PREVIEW_MAX_SIDE / max(img.size))
    pv = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS) if s < 1 else img
    buf = io.BytesIO()
    pv.save(buf, "JPEG", quality=82)
    boxes = [{"bbox": [int(v * s) for v in l["bbox"]], "text": l["text"], "confidence": l["confidence"]} for l in lines]
    return {"image": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(),
            "width": pv.width, "height": pv.height, "boxes": boxes}


HEADLINES = {
    "CERTIFICATE": "Relevant: this is a certificate.",
    "ACADEMIC_RECORD": "Relevant: this is an academic record (grade sheet, transcript or academic letter).",
    "OTHER_DOCUMENT": "Not relevant: this is a document, but not an academic credential.",
    "RANDOM_PHOTO": "Not relevant: this is not a document.",
}


DEMO_DIR = BASE_DIR / "demo_samples"


@app.get("/api/samples")
def list_samples():
    """Files in demo_samples/, offered as one-click samples on the upload page."""
    if not DEMO_DIR.exists():
        return []
    files = [p for p in sorted(DEMO_DIR.iterdir()) if p.is_file()]
    files += [p for d in sorted(DEMO_DIR.iterdir()) if d.is_dir() for p in sorted(d.iterdir())
              if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".pdf")]
    return [{"name": p.relative_to(DEMO_DIR).as_posix(), "size": p.stat().st_size} for p in files if not p.name.startswith(".")]


@app.get("/api/samples/{name:path}")
def get_sample(name: str):
    from fastapi.responses import FileResponse
    p = (DEMO_DIR / name).resolve()
    if DEMO_DIR.resolve() not in p.parents or not p.is_file():  # no path traversal
        raise HTTPException(status_code=404, detail="Sample not found.")
    return FileResponse(p, filename=p.name)


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """Accept any upload, check the file type, classify the document, extract fields."""
    t0 = time.perf_counter()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 25 MB.")
    mime, total_pages, pages = _load_pages(data)
    timings = {"decode": round((time.perf_counter() - t0) * 1000)}

    page_results = []
    for i, img in enumerate(pages):
        t = time.perf_counter()
        ocr = ocr_service.extract_text_and_layout(img)
        t_ocr = time.perf_counter()
        cls = doc_module.predict(img, ocr_text=ocr["full_text"])
        t_cls = time.perf_counter()
        page_results.append({"img": img, "ocr": ocr, "cls": cls})
        if i == 0:
            timings["ocr"] = round((t_ocr - t) * 1000)
            timings["classification"] = round((t_cls - t_ocr) * 1000)

    first = page_results[0]
    cls, ocr = first["cls"], first["ocr"]
    t = time.perf_counter()
    if cls["is_relevant"]:
        extraction = field_extractor.extract(ocr["lines"], cls["document_type"])
        # a multi-page record: pull fields the first page lacked from later relevant pages
        have = {f["key"] for f in extraction["fields"]}
        for pr in page_results[1:]:
            if pr["cls"]["is_relevant"]:
                more = field_extractor.extract(pr["ocr"]["lines"], pr["cls"]["document_type"])
                extraction["fields"] += [f for f in more["fields"] if f["key"] not in have]
                have |= {f["key"] for f in more["fields"]}
                if not extraction["table"] and more["table"]:
                    extraction["table"] = more["table"]
    else:
        extraction = {"fields": [], "table": None}
    timings["field_extraction"] = round((time.perf_counter() - t) * 1000)

    experimental = None
    if cls["is_relevant"]:
        try:
            tr = tamper_module.predict(np.array(first["img"]))
            experimental = {"tampering": {k: tr.get(k) for k in ("status", "is_tampered", "tampering_probability", "suspicious_regions_count")}}
        except Exception:
            experimental = None
    timings["total"] = round((time.perf_counter() - t0) * 1000)

    return {
        "document_name": file.filename,
        "file_type": mime,
        "page_count": total_pages,
        "pages_analyzed": len(pages),
        "verdict": {"is_relevant": cls["is_relevant"], "label": cls["label"], "headline": HEADLINES[cls["document_type"]]},
        "classification": cls,
        "fields": extraction["fields"],
        "table": extraction["table"],
        "ocr": {"engine": ocr["engine"], "word_count": ocr["word_count"], "average_confidence": ocr["average_confidence"],
                "text": ocr["full_text"][:3000]},
        "preview": _preview(first["img"], ocr["lines"]),
        "pages": [{"page": i + 1, "document_type": pr["cls"]["document_type"], "label": pr["cls"]["label"],
                   "confidence": pr["cls"]["confidence"], "is_relevant": pr["cls"]["is_relevant"]}
                  for i, pr in enumerate(page_results)],
        "experimental": experimental,
        "timings_ms": timings,
    }


@app.post("/api/verify/cross-document")
def verify_cross_document(payload: Dict[str, Any]):
    """
    Cross-document portfolio consistency verification.
    Expects payload: {"documents": [{"doc_id": str, "doc_type": str, "entities": dict, "text": str}]}
    """
    docs = payload.get("documents", [])
    if not docs:
        raise HTTPException(status_code=400, detail="Payload must contain a non-empty 'documents' list.")
    
    result = cross_verifier.verify_portfolio(docs)
    
    # Run evidence fusion on portfolio
    signals = {
        "cross_doc_consistency": result["consistency_score"],
        "field_anomalies_count": result["conflicts_count"],
        "tampering_probability": 0.05,
        "issuer_match": True,
        "ocr_confidence": 0.95
    }
    fusion = fuse(signals)
    result["portfolio_fusion"] = fusion
    return result


@app.post("/api/lor/analyze")
def analyze_lor_endpoint(payload: Dict[str, Any]):
    """
    Recommendation Letter semantic & plagiarism analysis.
    Expects payload: {"text": str, "reference_profile": Optional[dict]}
    """
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text field cannot be empty.")
    ref_prof = payload.get("reference_profile")
    return lor_analyzer.analyze_lor(text, reference_profile=ref_prof)


if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
