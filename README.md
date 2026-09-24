# 🛡️ Vellum &mdash; Multi-Modal AI Document Verification Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-DirectML-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

> **Vellum** is an enterprise-grade, multi-modal AI platform for academic credential verification, document forgery detection, and cross-document forensic intelligence. Inspired by luxury editorial interfaces ([Clarvos](https://www.clarvos.com/)), Vellum bridges deep neural inspection with a tactile, human-centered review workspace.

---

## Working Prototype (AI course demo)

**What it does:** upload any image or PDF. The model decides which of 4 classes it is, and for relevant documents it reads the fields out.

| Class | Meaning | Result |
|---|---|---|
| Certificate | degree, course completion, internship, participation | Relevant, fields extracted |
| Academic record | grade sheet, CGPA, transcript, completion or bonafide letter, LOR | Relevant, fields + course table extracted |
| Unrelated document | invoice, form, memo, article | Rejected |
| Not a document | random photo | Rejected |

**How it classifies:** three models fused by a weighted average of their probabilities.
1. EfficientNet-B0, ImageNet-pretrained, fine-tuned on our dataset (`ml/document_classifier/train.py`)
2. CLIP ViT-B/32 zero-shot (`ml/document_classifier/clip_branch.py`), covers real-world scans
3. TF-IDF + logistic regression on the RapidOCR text (`ml/document_classifier/text_model.py`)

**Measured results** (`python -m ml.document_classifier.evaluate`, numbers in `models/document_classifier_metrics.json`):
- Fused: 100% on the 448-image held-out test split, 6/6 on genuine real-world diplomas and records
- Image CNN alone: 100% test, 1/6 real-world. CLIP alone: 87.1% test, 6/6 real-world. Text alone: 96.7% test

### Run the demo (Windows)

```powershell
# one-time setup
uv venv .venv --python 3.12            # or: python -m venv .venv
.venv\Scripts\python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
.venv\Scripts\python -m pip install -r backend/requirements.txt transformers
.venv\Scripts\python scripts/download_models.py   # CLIP weights, 605 MB
cd frontend; npm install; cd ..

# every time
powershell -ExecutionPolicy Bypass -File start_demo.ps1   # starts API :8000 + UI :5173, opens the browser
powershell -ExecutionPolicy Bypass -File stop_demo.ps1
```

Test files for the live demo are in `demo_samples/` (one click each on the upload page). `demo_samples/real_world/` holds genuine scans from Wikimedia Commons that the model never trained on.

**Rebuild everything from scratch:** `python scripts/build_classifier_dataset.py`, `python -m ml.document_classifier.train`, `python -m ml.document_classifier.text_model ocr 150 0 1`, `python -m ml.document_classifier.text_model train`, `python -m ml.document_classifier.evaluate`.

**Tests:** `.venv\Scripts\python -m pytest tests/test_analyze.py -q` (17 tests: every class, PDF, field values, rejection, path traversal).

**Slides:** `presentation/Vellum-AI-Prototype.pptx`, rebuilt by `python presentation/build_deck.py`.

---

## 🏛️ Key Capabilities

* **Multi-Modal Neural Inspection**: Fuses 5 specialized neural models to evaluate pixel tampering, cursive signatures, wax/ink seals, entity consistency, and document classification in real time.
* **Optical Forensic Stage & 2.5x Loupe**: Interactive certificate mat with 4 layer overlays (Pristine Scan, UNet Heatmap, OCR Anchors, and Error Level Analysis Loupe).
* **Cross-Document Entity Graph**: Automatically cross-verifies candidate names, registration IDs, GPA, and conferral dates across Diplomas, Transcripts, and Letters of Recommendation (LOR).
* **Cryptographic Audit Ledger**: SHA-256 hash-chained immutable audit trail recording intake telemetry, neural weights, and investigator decisions for strict compliance.
* **Luxury Editorial UX**: Tactile card depth, warm ambient lighting, embossed physical paper shaders, and a live **Typography Preset Switcher** (*Instrument Serif*, *Newsreader*, *Cormorant Garamond*, *Fraunces*).

---

## 🔬 Multi-Modal Forensic Architecture

`
                                  [ Upload Document / PDF ]
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │  FastAPI Gateway & Ingestion  │
                             └───────────────┬───────────────┘
                                             │
                   ┌─────────────────────────┼─────────────────────────┐
                   ▼                         ▼                         ▼
        ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
        │  Document Classifier │   │    OCR & NER Unit   │   │  UNet Pixel Splicing│
        │    (ResNet / ViT)   │   │ (Tesseract/GraphNER)│   │  Tamper Localization│
        └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                   │                         │                         │
                   │                         ▼                         │
                   │              ┌─────────────────────┐              │
                   │              │ Cross-Doc Verifier  │              │
                   │              │(Diploma vs LORs)    │              │
                   │              └──────────┬──────────┘              │
                   │                         │                         │
                   ▼                         ▼                         ▼
        ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
        │   Siamese Network   │   │   Hough Transform   │   │ Error Level Analysis│
        │Signature Verification│  │  Official Seal Auth │   │  (2.5x Optic Loupe) │
        └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                   │                         │                         │
                   └─────────────────────────┼─────────────────────────┘
                                             ▼
                             ┌───────────────────────────────┐
                             │ Multi-Modal Evidence Fusion   │
                             │ (Confidence & Risk Scorer)    │
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │   SHA-256 Audit Trail Ledger  │
                             └───────────────────────────────┘
`

---

## 🖥️ Screen Gallery & Workspaces

The platform provides 13 fully developed, interactive screens:

| # | Screen | Description |
|---|--------|-------------|
| **1** | **Login Gateway** | RBAC login supporting *Fraud Investigator*, *Admissions Reviewer*, and *Platform Admin* personas. |
| **2** | **Executive Dashboard** | High-level triage overview, surveillance telemetry, queue filters, and KPI cards with tactile depth. |
| **3** | **Verification Workspace** | Core dual-pane review console featuring the physical document canvas and evidence telemetry. |
| **4** | **Optical Canvas & Loupe** | Multi-layer viewport with 2.5x magnification loupe, pixel ELA, and guilloché frame inspections. |
| **5** | **Evidence Panel** | Neural verdict breakdown, risk gauge, and progressive disclosure for signal contribution weights. |
| **6** | **Signature & Seal Matrix** | Siamese cosine similarity matching and Hough transform circular seal geometry validation. |
| **7** | **Entity Extraction Graph** | Tokenized field extraction matching certificate numbers against official registrar databases. |
| **8** | **Document Intake** | Multi-file intake dropzone with instant format validation, SHA-256 hashing, and batch queuing. |
| **9** | **Processing Pipeline** | Live 7-stage neural execution visualization with DirectML hardware telemetry. |
| **10** | **Decision Dock** | Floating tactile action dock for single-click approvals, committee escalations, or fraud rejections. |
| **11** | **History & Ledger** | Historical registry of verified credentials with multi-filter search and export capabilities. |
| **12** | **Audit Trail** | Cryptographically chained ledger tracking genesis blocks, forensic milestones, and decision actors. |
| **13** | **Analytics & Admin** | Platform fraud trends, institutional risk distribution, SIEM webhooks, and team management. |

---

## ⌨️ Keyboard Navigation Shortcuts

Accelerate credential triage using instantaneous hotkeys:

| Key | Action |
|:---:|--------|
| <kbd>1</kbd> | Switch to **Pristine Document Scan** layer |
| <kbd>2</kbd> | Toggle **UNet Tampering Heatmap** overlay |
| <kbd>3</kbd> | Toggle **OCR Spatial Entity Anchors** |
| <kbd>4</kbd> | Open **2.5x Optical Forensic Loupe & ELA** |
| <kbd>A</kbd> | **Approve Credential** (Verified Genuine) |
| <kbd>E</kbd> | **Escalate Credential** (Manual Committee Review) |
| <kbd>R</kbd> | **Reject Credential** (Flag Fraud Anomaly) |
| <kbd>J</kbd> | Next Dossier in Triage Queue |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Node.js** v18+ & **npm**
- **Python** 3.10+ (Optional for backend ML execution)
- Modern browser (Chrome, Edge, Firefox, Safari)

---

### 2. Frontend Setup (React 19 + Vite)

`ash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
`

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

### 3. Backend & ML Setup (FastAPI + DirectML)

`ash
# Create and activate Python virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
`

Interactive API Swagger documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 📂 Repository Structure

`
Vellum-AI/
├── backend/                  # FastAPI REST API backend service
│   ├── app.py                # Core API endpoints & orchestration
│   └── requirements.txt      # Python dependencies
├── data/                     # Synthetic test datasets & annotations
│   ├── raw/                  # Reference document corpora (FUNSD, etc.)
│   └── synthetic/            # Generated academic certificates & LORs
├── docs/                     # Design systems, UX research logs & specs
│   ├── design_system.md      # Vellum typography & tactile token specs
│   ├── models/               # Architectural specs for individual ML models
│   └── uiux_research/        # 500+ reference UX research analysis
├── frontend/                 # React 19 + Vite + Tailwind CSS application
│   ├── src/
│   │   ├── components/       # Common tactile UI components (Badge, Button, KpiCard, Modal)
│   │   ├── features/         # Workspace features (DocumentCanvas, Loupe, EvidencePanel)
│   │   ├── layouts/          # Floating AppLayout with Live Typography Switcher
│   │   ├── pages/            # 13 Application screens
│   │   └── styles/           # globals.css with editorial typography CSS variables
│   └── package.json
├── ml/                       # Multi-Modal ML neural pipelines
│   ├── cross_verification/   # Cross-document consistency verification
│   ├── document_classifier/  # Document type identification (PyTorch)
│   ├── fusion/               # Evidence fusion scoring algorithms
│   ├── nlp/                  # Entity extraction & LOR sentiment NLP
│   ├── ocr/                  # Optical character recognition services
│   ├── signature/            # Siamese CNN signature verification
│   ├── stamp/                # Hough circle transform seal validation
│   ├── tampering/            # UNet pixel-level tampering detector
│   └── utils/                # DirectML hardware detection & image helpers
├── models/                   # PyTorch neural weights (.pt) & model registry
├── scripts/                  # Dataset generation, splitting & validation utilities
└── tests/                    # Automated unit & pipeline integration tests
`

---

## 🎨 Editorial Typography System

Vellum features a live runtime typography preset engine. Test it dynamically using the **Aa Font** menu in the top bar:

1. **Instrument Serif (Clarvos Default)**: High-contrast luxury editorial display serif with dramatic italics.
2. **Newsreader (Academic)**: Optical-sized archival serif engineered for scholarly certificates and legal documents.
3. **Cormorant Garamond (Vogue Heritage)**: Classical high-fashion hairline serif with traditional Roman proportions.
4. **Fraunces (Warm Contemporary)**: Soft-serif display typography with warm curves and tactile personality.

---

## 🛡️ License

This project is licensed under the [MIT License](LICENSE).
