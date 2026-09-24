"""
OCR and Document Layout Service.

Engine order: RapidOCR (PaddleOCR models on ONNX Runtime, pip-only, no system binary),
then PyTesseract if a Tesseract binary is installed. If neither is available the service
returns an EMPTY result with engine "none". It never fabricates text.

Output of extract_text_and_layout():
  full_text           lines joined top-to-bottom, left-to-right
  lines               [{text, bbox [x1, y1, x2, y2], confidence}]
  word_count
  average_confidence
  engine
"""

from pathlib import Path
from typing import Any, Dict, List, Union

import cv2
import numpy as np
from PIL import Image

MAX_OCR_SIDE = 2400
MIN_OCR_SIDE = 1800  # small phone photos are upscaled: tiny glyphs lose word spaces and whole table rows


def _to_rgb_array(image_input: Union[str, Path, Image.Image, np.ndarray]) -> np.ndarray:
    if isinstance(image_input, (str, Path)):
        return np.array(Image.open(image_input).convert("RGB"))
    if isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"))
    if isinstance(image_input, np.ndarray):
        if image_input.ndim == 2:
            return cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
        if image_input.shape[2] == 4:
            return cv2.cvtColor(image_input, cv2.COLOR_RGBA2RGB)
        return image_input
    raise ValueError(f"Unsupported image input type: {type(image_input)}")


def _order_lines(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort boxes into reading order: group by row (vertical overlap), then left to right."""
    if not lines:
        return lines
    lines = sorted(lines, key=lambda l: (l["bbox"][1] + l["bbox"][3]) / 2)
    rows, current = [], [lines[0]]
    for l in lines[1:]:
        prev = current[-1]
        h = max(1, prev["bbox"][3] - prev["bbox"][1])
        if abs((l["bbox"][1] + l["bbox"][3]) / 2 - (prev["bbox"][1] + prev["bbox"][3]) / 2) < 0.5 * h:
            current.append(l)
        else:
            rows.append(current)
            current = [l]
    rows.append(current)
    out = []
    for r in rows:
        out.extend(sorted(r, key=lambda l: l["bbox"][0]))
    return out


class OCRService:
    def __init__(self):
        self.engine_name = "none"
        self.rapid = None
        self.pytesseract = None
        try:
            from rapidocr_onnxruntime import RapidOCR
            self.rapid = RapidOCR()
            self.engine_name = "RapidOCR"
        except Exception:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self.pytesseract = pytesseract
                self.engine_name = "PyTesseract"
            except Exception:
                pass

    def extract_text_and_layout(self, image_input) -> Dict[str, Any]:
        img = _to_rgb_array(image_input)
        h, w = img.shape[:2]
        scale = 1.0
        if max(h, w) > MAX_OCR_SIDE:
            scale = MAX_OCR_SIDE / max(h, w)
        elif max(h, w) < MIN_OCR_SIDE:
            scale = MIN_OCR_SIDE / max(h, w)
        if scale != 1.0:
            interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=interp)

        lines: List[Dict[str, Any]] = []
        if self.rapid is not None:
            result, _ = self.rapid(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            for box, text, conf in result or []:
                xs, ys = [p[0] for p in box], [p[1] for p in box]
                lines.append({"text": str(text).strip(),
                              "bbox": [int(min(xs) / scale), int(min(ys) / scale), int(max(xs) / scale), int(max(ys) / scale)],
                              "confidence": round(float(conf), 3)})
        elif self.pytesseract is not None:
            d = self.pytesseract.image_to_data(img, output_type=self.pytesseract.Output.DICT)
            for i in range(len(d["text"])):
                t, c = d["text"][i].strip(), float(d["conf"][i])
                if t and c > 0:
                    x, y, bw, bh = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
                    lines.append({"text": t, "bbox": [int(x / scale), int(y / scale), int((x + bw) / scale), int((y + bh) / scale)],
                                  "confidence": round(c / 100.0, 3)})

        lines = [l for l in lines if l["text"]]
        lines = _order_lines(lines)
        avg = sum(l["confidence"] for l in lines) / len(lines) if lines else 0.0
        return {
            "full_text": "\n".join(l["text"] for l in lines),
            "lines": lines,
            "word_count": sum(len(l["text"].split()) for l in lines),
            "average_confidence": round(avg, 3),
            "engine": self.engine_name,
        }


_ocr_service_instance = None


def get_ocr_service() -> OCRService:
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    return _ocr_service_instance


if __name__ == "__main__":
    import sys
    ocr = get_ocr_service()
    print("OCR Engine:", ocr.engine_name)
    if len(sys.argv) > 1:
        print(ocr.extract_text_and_layout(sys.argv[1])["full_text"])
