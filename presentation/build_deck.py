"""
Builds presentation/Vellum-AI-Presentation.pptx from the real screenshots in presentation/shots/
and the measured metrics in models/document_classifier_metrics.json.

  python presentation/build_deck.py
"""

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
SHOTS = BASE / "presentation" / "shots"
OUT = BASE / "presentation" / "Vellum-AI-Presentation.pptx"
METRICS = json.load(open(BASE / "models" / "document_classifier_metrics.json"))

# Palette and type follow the running app (frontend/tailwind.config.js, globals.css)
INK = RGBColor(0x14, 0x14, 0x16)       # ink, dark slides and headings
PAPER = RGBColor(0xFA, 0xF8, 0xF5)     # canvas, slide background
PARCH = RGBColor(0xF4, 0xF0, 0xE8)     # canvas-subtle panels
SAND = RGBColor(0xEC, 0xE7, 0xDD)      # canvas-sand, highlighted panels
SEAL = RGBColor(0x9E, 0x2A, 0x2B)      # accent-crimson, rejected
GOLD = RGBColor(0xC2, 0x9B, 0x38)      # accent-gold
GREEN = RGBColor(0x1E, 0x7A, 0x4F)
MUTED = RGBColor(0x71, 0x71, 0x7A)
ON_DARK = RGBColor(0xEC, 0xE7, 0xDD)
ON_DARK_MUTED = RGBColor(0xA1, 0xA1, 0xAA)
HEAD, BODY = "Segoe UI Semibold", "Segoe UI"   # Inter is not installed here; Segoe UI is the app's own fallback

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


def bg(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def text(slide, x, y, w, h, s, size=16, color=INK, bold=False, font=BODY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    lines = s if isinstance(s, list) else [s]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size, r.font.bold, r.font.name, r.font.italic = Pt(size), bold, font, italic
        r.font.color.rgb = color
    return tb


def bullets(slide, x, y, w, h, items, size=16, color=INK, gap=8):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        if isinstance(it, tuple):
            r = p.add_run(); r.text = it[0] + "  "; r.font.bold = True
            r.font.size, r.font.name = Pt(size), BODY; r.font.color.rgb = color
            r = p.add_run(); r.text = it[1]
        else:
            r = p.add_run(); r.text = it
        r.font.size, r.font.name = Pt(size), BODY
        r.font.color.rgb = color
    return tb


def card(slide, x, y, w, h, fill=PARCH):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.adjustments[0] = 0.06
    s.fill.solid(); s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def dot(slide, x, y, d, color, label=""):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, d, d)
    s.fill.solid(); s.fill.fore_color.rgb = color
    s.line.fill.background()
    if label:
        tf = s.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = label
        r.font.size, r.font.bold, r.font.name = Pt(16), True, BODY
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return s


def picture(slide, path, x, y, max_w, max_h):
    iw, ih = Image.open(path).size
    s = min(max_w / iw, max_h / ih)
    w, h = int(iw * s), int(ih * s)
    pic = slide.shapes.add_picture(str(path), x + (max_w - w) // 2, y + (max_h - h) // 2, w, h)
    pic.line.color.rgb = RGBColor(0xD6, 0xD2, 0xC8)
    pic.line.width = Pt(0.75)
    return pic


def title(slide, s, sub=None, color=INK):
    text(slide, Inches(0.6), Inches(0.45), Inches(12), Inches(0.8), s, size=34, bold=True, font=HEAD, color=color)
    if sub:
        text(slide, Inches(0.6), Inches(1.2), Inches(12), Inches(0.5), sub, size=16, color=MUTED)


pct = lambda v: f"{v * 100:.1f}%"
m0 = METRICS

# 1. Title ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, INK)
dot(s, Inches(0.6), Inches(0.7), Inches(0.9), GOLD, "V")
text(s, Inches(0.6), Inches(2.1), Inches(11.5), Inches(1.3), "Vellum AI", size=60, bold=True, font=HEAD, color=PAPER)
text(s, Inches(0.6), Inches(3.3), Inches(11.5), Inches(1.2),
     "Multi-modal AI document verification and credential forensic intelligence", size=24, color=ON_DARK)
text(s, Inches(0.6), Inches(5.4), Inches(11.5), Inches(0.5), "BCSE306L Artificial Intelligence  |  Course project prototype", size=16, color=ON_DARK_MUTED)
text(s, Inches(0.6), Inches(5.85), Inches(11.5), Inches(0.5), "VIT Vellore  |  Fall Semester 2026-27", size=16, color=ON_DARK_MUTED)

# 2. What changed after the first review -------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "What changed after the first review", "Reviewer feedback on the left, what we built in response on the right")
card(s, Inches(0.6), Inches(2.0), Inches(4.3), Inches(4.9))
text(s, Inches(0.9), Inches(2.2), Inches(3.8), Inches(0.5), "Review feedback", size=20, bold=True, font=HEAD, color=SEAL)
bullets(s, Inches(0.9), Inches(2.85), Inches(3.8), Inches(3.9), [
    "Make clear which files can be uploaded",
    "Three models processing every upload is wasteful",
    "The best model should be chosen automatically",
    "Explain the actual ML, not just show screens",
], size=15)
card(s, Inches(5.2), Inches(2.0), Inches(7.5), Inches(4.9), fill=SAND)
text(s, Inches(5.5), Inches(2.2), Inches(7.0), Inches(0.5), "What we changed", size=20, bold=True, font=HEAD, color=GREEN)
bullets(s, Inches(5.5), Inches(2.85), Inches(7.0), Inches(3.9), [
    ("Early-exit cascade:", f"models run fastest first and the first one at least 90% sure answers, the rest never run. Still {pct(m0['cascade_test_accuracy'])} test, {pct(m0['cascade_real_world_accuracy'])} real scans"),
    ("Result page:", "shows the one model that decided, its confidence and its time"),
    ("OCR only when needed:", "a rejected photo never pays the seconds OCR costs"),
    ("Handbook page:", "accepted inputs, the four classes, every extracted field, each pipeline step"),
    ("Learn the ML:", "five explainer tabs, with live CNN feature maps from the real model"),
    ("Mock screens removed:", "every page left in the app runs on the real model"),
], size=14, gap=6)

# 2b. Problem ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "The problem", "Institutions receive thousands of uploaded documents and check each one by hand")
card(s, Inches(0.6), Inches(2.0), Inches(5.9), Inches(4.8))
text(s, Inches(0.9), Inches(2.2), Inches(5.4), Inches(0.5), "What happens today", size=20, bold=True, font=HEAD)
bullets(s, Inches(0.9), Inches(2.85), Inches(5.3), Inches(3.8), [
    "Students upload certificates, grade sheets and letters as photos or PDFs",
    "Many uploads are the wrong file: a selfie, an invoice, a random screenshot",
    "Staff open each file to check what it is and copy the name, register number and CGPA by hand",
    "Slow, error prone, and it does not scale at admission or placement time",
], size=16)
card(s, Inches(6.85), Inches(2.0), Inches(5.9), Inches(4.8), fill=SAND)
text(s, Inches(7.15), Inches(2.2), Inches(5.4), Inches(0.5), "What Vellum does", size=20, bold=True, font=HEAD, color=GREEN)
bullets(s, Inches(7.15), Inches(2.85), Inches(5.3), Inches(3.8), [
    ("1. Accepts anything:", "any image format or a multi-page PDF, and rejects unsupported files with a clear message"),
    ("2. Decides what it is:", "certificate, academic record, unrelated document, or not a document"),
    ("3. Reads it:", "OCR plus field extraction pulls out name, register number, institution, CGPA, dates and the course table"),
], size=16)

# 3. Classes ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "Four classes", "Two are relevant credentials, two are rejected")
classes = [
    ("Certificate", "Degree, course completion, internship, participation, provisional certificates", GREEN, "Relevant"),
    ("Academic record", "Grade sheet, mark sheet, CGPA statement, transcript, completion and bonafide letters, LORs", GREEN, "Relevant"),
    ("Unrelated document", "A real document that is not a credential: invoice, form, memo, article, statement", SEAL, "Rejected"),
    ("Not a document", "A random photo from the internet: people, animals, scenes, objects", SEAL, "Rejected"),
]
for i, (n, d, c, tag) in enumerate(classes):
    x = Inches(0.6) + i * Inches(3.1)
    card(s, x, Inches(2.1), Inches(2.9), Inches(4.3))
    dot(s, x + Inches(0.3), Inches(2.4), Inches(0.7), c, str(i + 1))
    text(s, x + Inches(0.3), Inches(3.3), Inches(2.4), Inches(0.9), n, size=20, bold=True, font=HEAD)
    text(s, x + Inches(0.3), Inches(4.15), Inches(2.4), Inches(1.6), d, size=14, color=MUTED)
    text(s, x + Inches(0.3), Inches(5.85), Inches(2.4), Inches(0.4), tag, size=14, bold=True, color=c)

# 4. Pipeline ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "How the model works", "One upload goes through five stages")
steps = [
    ("Intake", "Magic-byte check. Images decoded with EXIF rotation, PDF pages rendered at 300 DPI"),
    ("OCR", "RapidOCR (PaddleOCR models on ONNX Runtime) reads every text line with its box"),
    ("Three classifiers", "Fine-tuned CNN on pixels, zero-shot CLIP on pixels, TF-IDF model on the OCR text"),
    ("Cascade", "Fastest model first; the first one at least 90% confident decides the class"),
    ("Field extraction", "For relevant documents only: layout-aware rules pull out the fields"),
]
for i, (n, d) in enumerate(steps):
    x = Inches(0.6) + i * Inches(2.5)
    dot(s, x, Inches(2.2), Inches(0.75), INK if i != 3 else GOLD, str(i + 1))
    if i < 4:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + Inches(0.95), Inches(2.43), Inches(1.3), Inches(0.3))
        a.fill.solid(); a.fill.fore_color.rgb = RGBColor(0xC9, 0xC4, 0xB8); a.line.fill.background()
    text(s, x, Inches(3.2), Inches(2.3), Inches(0.5), n, size=18, bold=True, font=HEAD)
    text(s, x, Inches(3.75), Inches(2.25), Inches(2.4), d, size=14, color=MUTED)
card(s, Inches(0.6), Inches(5.9), Inches(12.1), Inches(1.0), fill=SAND)
text(s, Inches(0.9), Inches(6.0), Inches(11.6), Inches(0.8),
     "Stack: PyTorch, torchvision, Hugging Face Transformers, scikit-learn, RapidOCR, PyMuPDF, FastAPI backend, React + Vite + Tailwind frontend",
     size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE)

# 5. Three models ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "Why three models", "Each one covers a weakness of the others")
m = METRICS
rows = [
    ("Image CNN", "EfficientNet-B0, ImageNet pretrained, fine-tuned 12 epochs on our dataset",
     f"{pct(m['image_cnn_test_accuracy'])} test", f"{pct(m['image_cnn_real_world_accuracy'])} real scans"),
    ("CLIP zero-shot", "ViT-B/32 trained on 2 billion real image-text pairs, never saw our data",
     f"{pct(m['clip_zero_shot_test_accuracy'])} test", f"{pct(m['clip_zero_shot_real_world_accuracy'])} real scans"),
    ("OCR text model", "TF-IDF word and character n-grams + logistic regression on the OCR text",
     f"{pct(m.get('text_test_accuracy', 0))} test", "reads the words"),
    ("Cascade", f"CNN answered {m['cascade_test_answered_by']['image']} of {m['test_samples']} test images; CLIP answered {m['cascade_real_world_answered_by']['clip']} of {m['real_world_samples']} real scans",
     f"{pct(m['cascade_test_accuracy'])} test", f"{pct(m['cascade_real_world_accuracy'])} real scans"),
]
for i, (n, d, a, b) in enumerate(rows):
    y = Inches(1.95) + i * Inches(1.25)
    card(s, Inches(0.6), y, Inches(12.1), Inches(1.1), fill=PARCH if i < 3 else SAND)
    text(s, Inches(0.9), y + Inches(0.12), Inches(2.6), Inches(0.9), n, size=20, bold=True, font=HEAD,
         color=GREEN if i == 3 else INK, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(3.5), y + Inches(0.12), Inches(5.3), Inches(0.9), d, size=14, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(8.9), y + Inches(0.12), Inches(1.9), Inches(0.9), a, size=18, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(10.8), y + Inches(0.12), Inches(1.8), Inches(0.9), b, size=16, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

# 6. Dataset ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "Training data", "Built for this project, split before augmentation so no copy leaks across splits")
bullets(s, Inches(0.6), Inches(2.0), Inches(6.3), Inches(4.8), [
    ("Certificates:", "synthetic degree, completion, internship and participation certificates with varied templates, fonts, seals"),
    ("Academic records:", "synthetic grade sheets and mark sheets, completion and bonafide letters, 120 rendered LORs"),
    ("Unrelated documents:", "RVL-CDIP subset (15 document types), FUNSD forms, synthetic invoices, menus, articles"),
    ("Random photos:", "Flickr30k test photos and Imagenette"),
    ("Augmentation:", "phone-photo simulation (perspective, desk background, shadow, blur) and photocopy effects"),
], size=15)
split = [("Train", 1944), ("Validation", 407), ("Test", 448)]
for i, (n, v) in enumerate(split):
    y = Inches(2.0) + i * Inches(1.55)
    card(s, Inches(7.4), y, Inches(5.3), Inches(1.35))
    text(s, Inches(7.7), y + Inches(0.1), Inches(2.5), Inches(1.1), str(v), size=40, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(10.0), y + Inches(0.1), Inches(2.5), Inches(1.1), n + " images", size=18, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

# 7. Results ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "Results", "Measured on held-out data. The real-world set is only 6 scans and the fusion weights were tuned on these sets, so treat it as a sanity check.")
card(s, Inches(0.6), Inches(1.95), Inches(3.6), Inches(2.3))
text(s, Inches(0.9), Inches(2.1), Inches(3.1), Inches(1.1), pct(m["fused_test_accuracy"]), size=54, bold=True, font=HEAD, color=GREEN)
text(s, Inches(0.9), Inches(3.3), Inches(3.1), Inches(0.8), f"Test split accuracy, {m['test_samples']} images", size=15, color=MUTED)
card(s, Inches(0.6), Inches(4.45), Inches(3.6), Inches(2.3))
text(s, Inches(0.9), Inches(4.6), Inches(3.1), Inches(1.1), pct(m["fused_real_world_accuracy"]), size=54, bold=True, font=HEAD, color=GREEN)
text(s, Inches(0.9), Inches(5.8), Inches(3.1), Inches(0.8), f"Real-world scans, {m['real_world_samples']} genuine diplomas and records", size=15, color=MUTED)
cm = BASE / "models" / "document_classifier_confusion.png"
if cm.exists():
    picture(s, cm, Inches(4.6), Inches(1.8), Inches(8.1), Inches(5.3))

# 8+. One screenshot slide per class ---------------------------------------------------------------
shots = [
    ("certificate", "Class 1: Certificate", "A course completion certificate is recognised and its fields are read out"),
    ("record", "Class 2: Academic record", "A phone photo of a grade sheet: register number, semester, CGPA and course table extracted"),
    ("other", "Class 3: Unrelated document", "An invoice is a real document, but not a credential, so it is rejected"),
    ("photo", "Class 4: Not a document", "A random photo is rejected before any field extraction"),
    ("realworld", "Real-world scan", "A genuine university diploma the model has never seen, classified correctly"),
    ("pdf", "Multi-page PDF", "PDF uploads are rendered page by page and every page is classified"),
    ("reject", "Unsupported file", "Anything that is not an image or a PDF gets a clear error instead of a crash"),
]
for key, t, sub in shots:
    p = SHOTS / f"crop_{key}.png"
    if not p.exists():
        continue
    s = prs.slides.add_slide(BLANK); bg(s, PAPER)
    title(s, t, sub)
    picture(s, p, Inches(0.6), Inches(1.8), Inches(12.1), Inches(5.4))

# upload flow slide
if (SHOTS / "crop_upload.png").exists():
    s = prs.slides.add_slide(BLANK); bg(s, PAPER)
    title(s, "Step 1: Upload", "Drag in any image or PDF, or pick a file from the demo_samples folder")
    picture(s, SHOTS / "crop_upload.png", Inches(0.6), Inches(1.8), Inches(12.1), Inches(5.4))
    prs.slides._sldIdLst.insert(7, prs.slides._sldIdLst[-1])

# Live demo test files -------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, PAPER)
title(s, "Live demo: test files", "All in demo_samples/, one click each on the upload page")
demo = [
    ("01_certificate_course_completion.png", "Certificate", GREEN),
    ("02_certificate_degree.pdf", "Certificate (PDF)", GREEN),
    ("03_grade_sheet_phone_photo.jpg", "Academic record", GREEN),
    ("04_transcript_two_pages.pdf", "Academic record (2 pages)", GREEN),
    ("05_other_invoice.png", "Unrelated document", SEAL),
    ("06_other_scanned_form.jpg", "Unrelated document", SEAL),
    ("07 / 08_random_photo.jpg", "Not a document", SEAL),
    ("09_not_supported.txt", "Rejected: unsupported file", SEAL),
    ("real_world/ (6 real scans)", "Certificate / Academic record", GREEN),
]
for i, (f, r, c) in enumerate(demo):
    y = Inches(1.9) + i * Inches(0.57)
    card(s, Inches(0.6), y, Inches(12.1), Inches(0.5), fill=PARCH if i % 2 == 0 else PAPER)
    text(s, Inches(0.85), y, Inches(7.0), Inches(0.5), f, size=15, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(8.2), y, Inches(4.3), Inches(0.5), r, size=15, bold=True, color=c, anchor=MSO_ANCHOR.MIDDLE)

# Closing ---------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK); bg(s, INK)
text(s, Inches(0.6), Inches(0.8), Inches(12), Inches(0.9), "What we built", size=40, bold=True, font=HEAD, color=PAPER)
bullets(s, Inches(0.6), Inches(2.0), Inches(7.2), Inches(4.5), [
    "A working end-to-end prototype: upload, classify, extract, show",
    "Three models in an early-exit cascade: fine-tuned CNN, zero-shot CLIP, OCR text classifier",
    "Handles images, phone photos and multi-page PDFs, rejects everything else",
    "Every accuracy number on these slides was measured on held-out data",
], size=18, color=ON_DARK)
text(s, Inches(8.4), Inches(2.0), Inches(4.3), Inches(0.5), "Next steps", size=22, bold=True, font=HEAD, color=PAPER)
bullets(s, Inches(8.4), Inches(2.6), Inches(4.3), Inches(4), [
    "Train on real university documents",
    "Tampering and forgery detection",
    "Cross-document consistency checks",
    "Verification against issuer records",
], size=16, color=ON_DARK)
text(s, Inches(0.6), Inches(6.6), Inches(12), Inches(0.5), "Thank you", size=20, italic=True, font=HEAD, color=ON_DARK_MUTED)

prs.save(OUT)
print("saved", OUT, len(prs.slides), "slides")
