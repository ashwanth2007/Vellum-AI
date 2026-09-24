"""Document type classifier (4 classes, image CNN + CLIP zero-shot + OCR text, fused)."""

from ml.document_classifier.model import DOCUMENT_CLASSES, DocumentClassifier
from ml.document_classifier.predict import get_model, predict

__all__ = ["predict", "get_model", "DocumentClassifier", "DOCUMENT_CLASSES"]
