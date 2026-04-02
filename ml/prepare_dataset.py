"""
Скрипт для подготовки датасета: разделение на train/val/test
"""
from __future__ import annotations

import random
import shutil
from pathlib import Path
from typing import List

# Фиксируем seed для воспроизводимости
random.seed(42)


def split_dataset(
    source_dir: Path,
    output_dir: Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> None:
    """
    Разделяет датасет на train/val/test.
    
    Args:
        source_dir: Папка с исходными данными (Normal/, Tuberculosis/)
        output_dir: Папка для результата (будет создана структура train/val/test)
        train_ratio: Доля для обучения (по умолчанию 0.7)
        val_ratio: Доля для валидации (по умолчанию 0.15)
        test_ratio: Доля для теста (по умолчанию 0.15)
    """
    # Проверяем, что сумма равна 1.0
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, "Сумма пропорций должна быть 1.0"
    
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    
    # Маппинг старых имен на новые (для единообразия)
    class_mapping = {
        "Normal": "NORMAL",
        "Tuberculosis": "TUBERCULOSIS",
        "normal": "NORMAL",
        "tuberculosis": "TUBERCULOSIS",
        "NORMAL": "NORMAL",
        "TUBERCULOSIS": "TUBERCULOSIS",
    }
    
    # Создаем структуру папок
    splits = ["train", "val", "test"]
    for split in splits:
        for class_name in ["NORMAL", "TUBERCULOSIS"]:
            (output_dir / split / class_name).mkdir(parents=True, exist_ok=True)
    
    # Обрабатываем каждый класс
    for old_class_dir in source_dir.iterdir():
        if not old_class_dir.is_dir():
            continue
        
        old_class_name = old_class_dir.name
        new_class_name = class_mapping.get(old_class_name, old_class_name.upper())
        
        print(f"\nОбработка класса: {old_class_name} -> {new_class_name}")
        
        # Получаем все изображения
        image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
        images = [
            f for f in old_class_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not images:
            print(f"  ⚠️  Нет изображений в {old_class_dir}")
            continue
        
        # Перемешиваем для случайного разделения
        random.shuffle(images)
        
        total = len(images)
        train_count = int(total * train_ratio)
        val_count = int(total * val_ratio)
        test_count = total - train_count - val_count  # Остаток идет в test
        
        print(f"  Всего изображений: {total}")
        print(f"  Train: {train_count} ({train_count/total*100:.1f}%)")
        print(f"  Val: {val_count} ({val_count/total*100:.1f}%)")
        print(f"  Test: {test_count} ({test_count/total*100:.1f}%)")
        
        # Разделяем файлы
        train_files = images[:train_count]
        val_files = images[train_count:train_count + val_count]
        test_files = images[train_count + val_count:]
        
        # Копируем файлы
        for file in train_files:
            shutil.copy2(file, output_dir / "train" / new_class_name / file.name)
        
        for file in val_files:
            shutil.copy2(file, output_dir / "val" / new_class_name / file.name)
        
        for file in test_files:
            shutil.copy2(file, output_dir / "test" / new_class_name / file.name)
        
        print(f"  ✅ Скопировано: train={len(train_files)}, val={len(val_files)}, test={len(test_files)}")


def main() -> None:
    """Основная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Подготовка датасета: разделение на train/val/test")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("ml/data/chest_xray"),
        help="Исходная папка с данными (Normal/, Tuberculosis/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/data/chest_xray_split"),
        help="Выходная папка для разделенного датасета",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.7,
        help="Доля данных для обучения (по умолчанию 0.7)",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.15,
        help="Доля данных для валидации (по умолчанию 0.15)",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.15,
        help="Доля данных для теста (по умолчанию 0.15)",
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Подготовка датасета для обучения")
    print("=" * 60)
    print(f"Исходная папка: {args.source}")
    print(f"Выходная папка: {args.output}")
    print(f"Пропорции: train={args.train_ratio}, val={args.val_ratio}, test={args.test_ratio}")
    print("=" * 60)
    
    if not args.source.exists():
        print(f"❌ Ошибка: папка {args.source} не существует!")
        return
    
    # Проверяем наличие классов
    has_normal = any(
        d.is_dir() and d.name.lower() in ["normal", "normal"]
        for d in args.source.iterdir()
    )
    has_tb = any(
        d.is_dir() and "tuberculosis" in d.name.lower()
        for d in args.source.iterdir()
    )
    
    if not (has_normal or has_tb):
        print(f"❌ Ошибка: не найдены папки Normal/ и Tuberculosis/ в {args.source}")
        print(f"Найденные папки: {[d.name for d in args.source.iterdir() if d.is_dir()]}")
        return
    
    # Создаем выходную папку
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Разделяем датасет
    split_dataset(
        args.source,
        args.output,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
    )
    
    print("\n" + "=" * 60)
    print("✅ Готово! Датасет разделен.")
    print(f"Используйте для обучения: --data-dir {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()


