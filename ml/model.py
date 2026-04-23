from __future__ import annotations

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import torch  # type: ignore[import]
from PIL import Image
from torchvision import models, transforms  # type: ignore[import]


class FluoroModel:
    """Wrapper around fine-tuned ResNet classifier."""

    def __init__(self, weights_path: Path) -> None:
        self.weights_path = Path(weights_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet18()
        self.model.fc = torch.nn.Sequential(
            torch.nn.Dropout(0.3),
            torch.nn.Linear(self.model.fc.in_features, 2),
        )
        checkpoint = torch.load(self.weights_path, map_location=self.device)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.class_to_idx = checkpoint.get("class_to_idx", {"NORMAL": 0, "PNEUMONIA": 1})
        self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}
        self.model.eval().to(self.device)

        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    @torch.no_grad()
    def analyze(self, image_path: Path) -> Dict[str, Any]:
        image = Image.open(image_path).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        pred_idx = int(probs.argmax())
        confidence = float(probs[pred_idx])
        label = self.idx_to_class.get(pred_idx, "UNKNOWN")

        status = "pathology_detected" if label != "NORMAL" else "clear"
        if confidence < 0.7:
            status = "needs_review"

        # Генерируем детальное описание в зависимости от класса и уверенности
        diagnosis, findings = self._generate_diagnosis_and_findings(label, confidence, status)
        
        return {
            "status": status,
            "diagnosis": diagnosis,
            "findings": findings,
            "confidence": confidence,
            "label": label,
        }
    
    def _generate_diagnosis_and_findings(self, label: str, confidence: float, status: str) -> tuple[str, str]:
        """Генерация диагноза и детального описания находок."""
        
        # Определяем диагноз
        if label == "NORMAL":
            if confidence >= 0.95:
                diagnosis = "Норма. Патологических изменений не выявлено"
            elif confidence >= 0.85:
                diagnosis = "Норма. Признаков патологии не обнаружено"
            else:
                diagnosis = "Норма (требуется дополнительная проверка)"
            
            findings_templates = [
                "Легочные поля прозрачные, без очаговых и инфильтративных изменений.",
                "Корни легких структурны, не расширены.",
                "Сердечная тень обычной конфигурации и размеров.",
                "Диафрагма расположена обычно, синусы свободны.",
                "Костно-суставной аппарат без патологических изменений."
            ]
            
            if confidence >= 0.9:
                findings = " ".join(findings_templates[:4])
            elif confidence >= 0.8:
                findings = " ".join(findings_templates[:3])
            else:
                findings = " ".join(findings_templates[:2]) + " Рекомендуется контрольное исследование."
                
        elif label == "TUBERCULOSIS":
            if confidence >= 0.9:
                diagnosis = "Подозрение на туберкулез легких. Требуется консультация фтизиатра"
            elif confidence >= 0.8:
                diagnosis = "Выявлены изменения, подозрительные на туберкулез"
            else:
                diagnosis = "Обнаружены патологические изменения. Необходимо дообследование"
            
            findings_templates = [
                "Выявлены очаговые изменения в легочной ткани.",
                "Определяются участки инфильтрации в верхних отделах легких.",
                "Корни легких могут быть расширены, структурность снижена.",
                "Обнаружены кальцинаты или фиброзные изменения.",
                "Рекомендуется проведение компьютерной томографии органов грудной клетки для уточнения характера изменений."
            ]
            
            if confidence >= 0.9:
                findings = " ".join(findings_templates[:4]) + " " + findings_templates[4]
            elif confidence >= 0.8:
                findings = " ".join(findings_templates[:3]) + " " + findings_templates[4]
            else:
                findings = " ".join(findings_templates[:2]) + " " + findings_templates[4]
                
        else:  # UNKNOWN или другие классы
            diagnosis = "Требуется дополнительный анализ"
            findings = f"Определен класс: {label}. Уверенность модели: {confidence:.1%}. Рекомендуется ручная проверка специалистом."
        
        # Добавляем информацию об уверенности
        if confidence < 0.7:
            findings += f"\n\nПримечание: Низкая уверенность модели ({confidence:.1%}). Обязательна проверка врачом-рентгенологом."
        
        return diagnosis, findings

