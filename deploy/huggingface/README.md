---
title: Vellum AI
emoji: 📄
colorFrom: gray
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
short_description: Academic document classifier, CNN then CLIP then OCR cascade
---

# Vellum AI

Upload a certificate, grade sheet, letter or any other file. Three models are tried fastest first
(EfficientNet-B0 CNN, CLIP ViT-B/32, OCR plus a TF-IDF text model) and the first one that is at
least 90% sure answers. The "How the ML works" tabs explain each model.

Runs on the free CPU tier, so the first request after the Space wakes up takes longer while the
models load.

## Deploying

This folder holds the Space card, the Dockerfile and the pinned runtime requirements. The Space
repo root is the project root plus this README and the Dockerfile copied to the top level.
