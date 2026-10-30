# Vellum-AI on a Hugging Face Docker Space (free CPU tier: 2 vCPU, 16 GB RAM).
# One container: FastAPI serves /api and the built React app on port 7860.

# 1. Build the frontend
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2. Python runtime, CPU-only PyTorch
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /home/user/app

COPY --chown=user deploy/huggingface/requirements.txt requirements.txt
RUN pip install --no-cache-dir --user torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user backend/ backend/
COPY --chown=user ml/ ml/
COPY --chown=user models/ models/
COPY --chown=user scripts/download_models.py scripts/download_models.py
COPY --chown=user demo_samples/ demo_samples/
# CLIP weights (605 MB) come from the LAION repo at build time instead of being committed
RUN python scripts/download_models.py
COPY --from=web --chown=user /web/dist frontend/dist

EXPOSE 7860
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
