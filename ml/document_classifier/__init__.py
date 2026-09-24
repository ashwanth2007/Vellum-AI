"""Document type classifier. Imports are lazy so the OCR / text branch runs without torch loaded."""


def predict(*args, **kwargs):
    from ml.document_classifier.predict import predict as _predict
    return _predict(*args, **kwargs)


def get_model():
    from ml.document_classifier.predict import get_model as _get_model
    return _get_model()


DOCUMENT_CLASSES = ["CERTIFICATE", "ACADEMIC_RECORD", "OTHER_DOCUMENT", "RANDOM_PHOTO"]

__all__ = ["predict", "get_model", "DOCUMENT_CLASSES"]
