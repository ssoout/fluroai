"""Сервис для работы с ML моделью анализа флюорографии."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from ml.model import FluoroModel

# Глобальный экземпляр модели (загружается один раз при старте)
_model_instance: FluoroModel | None = None


def get_model() -> FluoroModel:
    """Получить экземпляр ML модели (singleton)."""
    global _model_instance
    if _model_instance is None:
        # Путь к обученной модели
        model_path = Path(__file__).parent.parent / "ml" / "models" / "resnet18_fluoro.pth"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Модель не найдена: {model_path}. "
                "Убедитесь, что модель обучена и сохранена."
            )
        _model_instance = FluoroModel(model_path)
    return _model_instance


def analyze_image(image_path: str | Path) -> Dict[str, Any]:
    """
    Анализ изображения флюорографии.
    
    Args:
        image_path: Путь к изображению
        
    Returns:
        Словарь с результатами анализа:
        - status: "clear", "pathology_detected", "needs_review"
        - findings: Текстовое описание находок
        - confidence: Уверенность модели (0.0-1.0)
    """
    model = get_model()
    image_path = Path(image_path)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Изображение не найдено: {image_path}")
    
    result = model.analyze(image_path)
    
    # Адаптируем формат для API
    return {
        "ai_status": result["status"],
        "ai_findings": result["findings"],
        "ai_confidence": result["confidence"],
        "ai_diagnosis": result.get("diagnosis", ""),  # Добавляем диагноз
        "label": result.get("label", ""),  # Добавляем метку класса
    }

