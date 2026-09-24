"""
Training script for the 4-class Document Type Classifier (visual branch).

  python -m ml.document_classifier.train
"""

import json
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
import yaml
from torch.utils.data import DataLoader

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.document_classifier.data import ManifestDataset, eval_transform, train_transform  # noqa: E402
from ml.document_classifier.model import DOCUMENT_CLASSES, DocumentClassifier  # noqa: E402

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def run_epoch(model, loader, device, criterion, optimizer=None, scaler=None, sched=None):
    train = optimizer is not None
    model.train(train)
    total, correct, loss_sum = 0, 0, 0.0
    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        with torch.set_grad_enabled(train), torch.autocast(device.type, enabled=device.type == "cuda"):
            logits, _ = model(x)
            loss = criterion(logits, y)
        if train:
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            sched.step()
        loss_sum += loss.item() * x.size(0)
        correct += (logits.argmax(1) == y).sum().item()
        total += x.size(0)
    return loss_sum / total, correct / total


def train():
    cfg = yaml.safe_load(open(CONFIG_PATH))
    tc = cfg["training"]
    size = cfg["input_size"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Device: {device} {torch.cuda.get_device_name(0) if device.type == 'cuda' else ''}", flush=True)

    train_ds = ManifestDataset("train", train_transform(size))
    val_ds = ManifestDataset("val", eval_transform(size))
    print(f"[*] Train {len(train_ds)} | Val {len(val_ds)}", flush=True)
    counts = torch.bincount(torch.tensor([DOCUMENT_CLASSES.index(r["label"]) for r in train_ds.rows]), minlength=4)
    weights = (counts.sum() / (len(counts) * counts.clamp(min=1))).float().to(device)
    print(f"[*] Class counts {counts.tolist()} -> loss weights {[round(w, 2) for w in weights.tolist()]}", flush=True)

    tl = DataLoader(train_ds, batch_size=tc["batch_size"], shuffle=True, num_workers=tc["num_workers"],
                    pin_memory=True, persistent_workers=True)
    vl = DataLoader(val_ds, batch_size=tc["batch_size"], shuffle=False, num_workers=tc["num_workers"],
                    pin_memory=True, persistent_workers=True)

    model = DocumentClassifier(num_classes=len(DOCUMENT_CLASSES), pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=tc["label_smoothing"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=tc["learning_rate"], weight_decay=tc["weight_decay"])
    sched = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=tc["learning_rate"],
                                                total_steps=tc["epochs"] * len(tl), pct_start=0.15)
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")

    ckpt = BASE_DIR / cfg["checkpoint"]
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    best, history = -1.0, []
    for ep in range(tc["epochs"]):
        t0 = time.time()
        tr_loss, tr_acc = run_epoch(model, tl, device, criterion, optimizer, scaler, sched)
        va_loss, va_acc = run_epoch(model, vl, device, criterion)
        history.append({"epoch": ep + 1, "train_loss": round(tr_loss, 4), "train_acc": round(tr_acc, 4),
                        "val_loss": round(va_loss, 4), "val_acc": round(va_acc, 4)})
        flag = ""
        if va_acc >= best:
            best = va_acc
            torch.save(model.state_dict(), ckpt)
            flag = "  <- saved"
        print(f"  Epoch {ep + 1:2d}/{tc['epochs']}  train loss {tr_loss:.4f} acc {tr_acc:.4f} | "
              f"val loss {va_loss:.4f} acc {va_acc:.4f}  ({time.time() - t0:.0f}s){flag}", flush=True)

    json.dump(history, open(BASE_DIR / "models" / "document_classifier_history.json", "w"), indent=2)
    print(f"[OK] Best val accuracy {best:.4f}, weights at {ckpt}", flush=True)


if __name__ == "__main__":
    train()
