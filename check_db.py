"""Скрипт для проверки подключения к БД и данных"""
import os
from pathlib import Path

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from backend.database import DATABASE_URL, SessionLocal, engine
from backend import models

print("=" * 60)
print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД")
print("=" * 60)

print(f"\nDATABASE_URL из переменной окружения: {os.getenv('DATABASE_URL', 'НЕ УСТАНОВЛЕНА')}")
print(f"Используется DATABASE_URL: {DATABASE_URL}")

if DATABASE_URL.startswith("postgresql"):
    db_info = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    print(f"✓ Используется PostgreSQL: {db_info}")
else:
    print(f"⚠ Используется SQLite: {DATABASE_URL}")
    sqlite_path = DATABASE_URL.replace("sqlite:///", "")
    if Path(sqlite_path).exists():
        print(f"  Файл SQLite существует: {sqlite_path}")
    else:
        print(f"  Файл SQLite НЕ существует: {sqlite_path}")

print("\n" + "=" * 60)
print("ПРОВЕРКА ДАННЫХ В БД")
print("=" * 60)

try:
    with SessionLocal() as db:
        # Проверяем пациентов
        patients = db.query(models.Patient).all()
        print(f"\nПациентов в БД: {len(patients)}")
        for p in patients:
            print(f"  - ID={p.id}, Имя={p.full_name}, Email={p.email}, Дата рождения={p.birth_date}")
        
        # Проверяем исследования
        studies = db.query(models.Study).all()
        print(f"\nИсследований в БД: {len(studies)}")
        for s in studies:
            print(f"  - ID={s.id}, Patient ID={s.patient_id}, Дата={s.taken_at}")
        
        # Проверяем результаты анализа
        results = db.query(models.AnalysisResult).all()
        print(f"\nРезультатов анализа в БД: {len(results)}")
        
except Exception as e:
    print(f"\n✗ ОШИБКА при проверке данных: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)


