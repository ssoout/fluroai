from __future__ import annotations

from typing import List, Dict, Any


RECENT_RESULTS: List[Dict[str, Any]] = [
    {
        "patient_name": "Ирина Смирнова",
        "taken_at": "2025-11-18T08:30:00",
        "status": "pathology_detected",
        "findings": "Подозрение на инфильтрацию верхней доли",
        "confidence": 0.82,
    },
    {
        "patient_name": "Андрей Ковалёв",
        "taken_at": "2025-11-18T09:45:00",
        "status": "clear",
        "findings": "Патологии не обнаружены",
        "confidence": 0.94,
    },
    {
        "patient_name": "Мария Кузнецова",
        "taken_at": "2025-11-17T14:10:00",
        "status": "needs_review",
        "findings": "Низкая уверенность модели",
        "confidence": 0.55,
    },
]


ALERTS: List[Dict[str, Any]] = [
    {
        "patient_name": "Мария Кузнецова",
        "taken_at": "2025-11-17T14:10:00",
        "reason": "Низкая уверенность анализа, требуется ручная проверка",
        "resolved": False,
    }
]


STATS: Dict[str, Any] = {
    "processed": 128,
    "pathology_count": 17,
    "manual_review": 5,
}

