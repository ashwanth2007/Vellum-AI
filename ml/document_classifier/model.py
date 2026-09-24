"""
Document Type Classification Model (visual branch).

Classes
  0 CERTIFICATE      degree, course-completion, internship, participation certificates
  1 ACADEMIC_RECORD  grade sheets, mark sheets, transcripts, CGPA / completion / bonafide letters, LORs
  2 OTHER_DOCUMENT   a real document that is not an academic credential (invoice, form, memo, article)
  3 RANDOM_PHOTO     anything that is not a document at all

Backbone: ImageNet-pretrained EfficientNet-B0 (torchvision), fine-tuned end to end.
forward() returns (logits, embedding) so older callers keep working.
"""

import torch
import torch.nn as nn
from torchvision import models

DOCUMENT_CLASSES = ["CERTIFICATE", "ACADEMIC_RECORD", "OTHER_DOCUMENT", "RANDOM_PHOTO"]
RELEVANT_CLASSES = {"CERTIFICATE", "ACADEMIC_RECORD"}
CLASS_LABELS = {
    "CERTIFICATE": "Certificate",
    "ACADEMIC_RECORD": "Academic record",
    "OTHER_DOCUMENT": "Unrelated document",
    "RANDOM_PHOTO": "Not a document",
}


class DocumentClassifier(nn.Module):
    def __init__(self, num_classes: int = 4, pretrained: bool = False):
        super().__init__()
        weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        net = models.efficientnet_b0(weights=weights)
        self.features = net.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc_embed = nn.Linear(1280, 256)
        self.dropout = nn.Dropout(0.3)
        self.fc_classifier = nn.Linear(256, num_classes)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(self.features(x)).flatten(1)
        return torch.relu(self.fc_embed(x))

    def forward(self, x: torch.Tensor):
        embed = self.extract_features(x)
        return self.fc_classifier(self.dropout(embed)), embed
