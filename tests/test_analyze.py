"""
End-to-end tests for POST /api/analyze using the files in demo_samples/.

  .venv/Scripts/python -m pytest tests/test_analyze.py -q
"""

import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient  # noqa: E402
from backend.app import app  # noqa: E402

client = TestClient(app)
DEMO = BASE_DIR / "demo_samples"

CASES = [
    ("01_certificate_course_completion.png", "CERTIFICATE"),
    ("02_certificate_degree.pdf", "CERTIFICATE"),
    ("03_grade_sheet_phone_photo.jpg", "ACADEMIC_RECORD"),
    ("04_transcript_two_pages.pdf", "ACADEMIC_RECORD"),
    ("05_other_invoice.png", "OTHER_DOCUMENT"),
    ("06_other_scanned_form.jpg", "OTHER_DOCUMENT"),
    ("07_random_photo.jpg", "RANDOM_PHOTO"),
    ("08_random_photo.jpg", "RANDOM_PHOTO"),
    ("real_world/real_01_degree_certificate_wales.jpg", "CERTIFICATE"),
    ("real_world/real_03_phd_diploma_marquette.jpg", "CERTIFICATE"),
    ("real_world/real_05_student_record_book.jpg", "ACADEMIC_RECORD"),
]


def post(name):
    p = DEMO / name
    with open(p, "rb") as f:
        return client.post("/api/analyze", files={"file": (p.name, f.read())})


@pytest.mark.parametrize("name,expected", CASES)
def test_classification(name, expected):
    r = post(name)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["classification"]["document_type"] == expected
    assert d["verdict"]["is_relevant"] == (expected in ("CERTIFICATE", "ACADEMIC_RECORD"))


def test_irrelevant_documents_get_no_fields():
    assert post("07_random_photo.jpg").json()["fields"] == []


def test_grade_sheet_fields():
    fields = {f["key"]: f["value"] for f in post("03_grade_sheet_phone_photo.jpg").json()["fields"]}
    assert fields["register_number"] == "19BEC8572"
    assert fields["cgpa"] == "7.02"
    assert fields["holder_name"] == "Meera Chatterjee"


def test_pdf_pages_and_table():
    d = post("04_transcript_two_pages.pdf").json()
    assert d["page_count"] == 2 and len(d["pages"]) == 2
    assert d["table"] and len(d["table"]["rows"]) == 11


def test_unsupported_file_rejected():
    r = post("09_not_supported.txt")
    assert r.status_code == 415
    assert "Unsupported" in r.json()["detail"]


def test_empty_file_rejected():
    r = client.post("/api/analyze", files={"file": ("empty.png", b"")})
    assert r.status_code == 400


def test_sample_listing_and_traversal_guard():
    names = [s["name"] for s in client.get("/api/samples").json()]
    assert "01_certificate_course_completion.png" in names
    assert client.get("/api/samples/../backend/app.py").status_code == 404
