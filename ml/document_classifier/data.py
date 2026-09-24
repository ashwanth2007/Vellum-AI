"""Dataset and transforms for the document classifier (reads data/classifier/manifest.csv)."""

import csv
from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from ml.document_classifier.model import DOCUMENT_CLASSES

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "classifier"
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


def letterbox(img: Image.Image, size: int) -> Image.Image:
    """Resize keeping aspect ratio, pad to a square, so documents keep their shape."""
    img = img.convert("RGB")
    w, h = img.size
    s = size / max(w, h)
    img = img.resize((max(1, int(w * s)), max(1, int(h * s))), Image.BILINEAR)
    canvas = Image.new("RGB", (size, size), (128, 128, 128))
    canvas.paste(img, ((size - img.size[0]) // 2, (size - img.size[1]) // 2))
    return canvas


class Letterbox:
    def __init__(self, size):
        self.size = size

    def __call__(self, img):
        return letterbox(img, self.size)


def train_transform(size: int):
    return transforms.Compose([
        Letterbox(size),
        transforms.RandomAffine(degrees=4, translate=(0.03, 0.03), scale=(0.9, 1.08)),
        transforms.ColorJitter(0.25, 0.25, 0.25, 0.03),
        transforms.RandomGrayscale(p=0.15),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])


def eval_transform(size: int):
    return transforms.Compose([Letterbox(size), transforms.ToTensor(), transforms.Normalize(MEAN, STD)])


def read_manifest(split: str):
    with open(DATA_DIR / "manifest.csv", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["split"] == split]


class ManifestDataset(Dataset):
    def __init__(self, split: str, transform):
        self.rows = read_manifest(split)
        self.transform = transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        img = Image.open(DATA_DIR / r["path"]).convert("RGB")
        return self.transform(img), DOCUMENT_CLASSES.index(r["label"])
