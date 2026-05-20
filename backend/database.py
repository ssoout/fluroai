from __future__ import annotations

import os
from datetime import datetime, date
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Попытка загрузить .env файл если установлен python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv не установлен, используем только переменные окружения

from backend import models

# Поддержка как SQLite (для разработки), так и PostgreSQL (для production)
# По умолчанию используем SQLite - проще и не требует настройки
# Для PostgreSQL установите переменную окружения DATABASE_URL 1488
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # По умолчанию используем SQLite - файл в папке backend
    f"sqlite:///{Path(__file__).parent / 'fluoro_backend.db'}"
)

# Выводим информацию о подключении (без пароля)
if DATABASE_URL.startswith("postgresql"):
    db_info = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    print(f"[DB] Используется PostgreSQL: {db_info}")
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    print(f"[DB] Используется SQLite: {DATABASE_URL}")
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

# Если используется PostgreSQL, убираем параметры специфичные для SQLite
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+psycopg2://"):
    # PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Проверка соединения перед использованием
        pool_size=5,
        max_overflow=10,
    )
else:
    # SQLite
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Инициализация базы данных - создание всех таблиц."""
    try:
        db_info = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL
        print(f"[DB] ===== ИНИЦИАЛИЗАЦИЯ БД =====")
        print(f"[DB] Подключение к базе данных: {db_info}")
        
        if DATABASE_URL.startswith("postgresql"):
            print(f"[DB] Используется PostgreSQL")
        else:
            print(f"[DB] Используется SQLite: {DATABASE_URL}")
        
        models.Base.metadata.create_all(bind=engine)
        print("[DB] ✓ Таблицы успешно созданы/проверены")
        
        # Проверяем подключение, делая простой запрос
        with SessionLocal() as test_db:
            try:
                count = test_db.query(models.Patient).count()
                print(f"[DB] ✓ Подключение работает. Текущее количество пациентов: {count}")
            except Exception as e:
                print(f"[DB] ⚠ Предупреждение при проверке подключения: {e}")
        
        print(f"[DB] ===== БД ГОТОВА =====")
    except Exception as e:
        print(f"[DB] ✗✗✗ ОШИБКА при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        raise


def seed_demo_data(force: bool = False) -> None:
    with SessionLocal() as db:
        try:
            patient_count = db.query(models.Patient).count()
            print(f"[DB] Текущее количество пациентов в БД: {patient_count}")
            
            if not force and patient_count > 0:
                print("[DB] Пропуск загрузки демо-данных (данные уже есть)")
                return

            # Очищаем таблицы при форсированной инициализации
            if force:
                print("[DB] Очистка существующих данных...")
                db.query(models.AnalysisResult).delete()
                db.query(models.Study).delete()
                db.query(models.Patient).delete()
                db.query(models.EmailTemplate).delete()
                db.commit()
                print("[DB] Данные очищены")
        except Exception as e:
            print(f"[DB] ОШИБКА при проверке данных: {e}")
            # Продолжаем, возможно таблицы еще не созданы

        patient_1 = models.Patient(
            full_name="Ирина Смирнова",
            email="irina.smirnova@example.com",
            birth_date=date(1985, 2, 11),
            medical_record_number="MRN-1001",
        )
        patient_2 = models.Patient(
            full_name="Андрей Ковалёв",
            email="andrey.kovalev@example.com",
            birth_date=date(1974, 9, 3),
            medical_record_number="MRN-1002",
        )
        patient_3 = models.Patient(
            full_name="Мария Кузнецова",
            email="maria.kuznetsova@example.com",
            birth_date=date(1990, 12, 21),
            medical_record_number="MRN-1003",
        )

        db.add_all([patient_1, patient_2, patient_3])
        db.flush()

        study_1 = models.Study(
            patient_id=patient_1.id,
            taken_at=datetime(2025, 11, 18, 8, 30),
            priority="urgent",
            notes="Повтор после лечения",
            image_path="samples/fluoro_001.png",
        )
        study_2 = models.Study(
            patient_id=patient_2.id,
            taken_at=datetime(2025, 11, 18, 9, 45),
            priority="routine",
            notes="Плановый осмотр",
            image_path="samples/fluoro_002.png",
        )
        study_3 = models.Study(
            patient_id=patient_3.id,
            taken_at=datetime(2025, 11, 17, 14, 10),
            priority="routine",
            notes="",
            image_path="samples/fluoro_003.png",
        )

        db.add_all([study_1, study_2, study_3])
        db.flush()

        result_1 = models.AnalysisResult(
            study_id=study_1.id,
            ai_status="pathology_detected",
            ai_diagnosis="Выявлены изменения, подозрительные на туберкулез",
            ai_findings="Выявлены очаговые изменения в легочной ткани. Определяются участки инфильтрации в верхних отделах легких.",
            ai_confidence=0.82,
        )
        result_2 = models.AnalysisResult(
            study_id=study_2.id,
            ai_status="clear",
            ai_diagnosis="Норма. Патологических изменений не выявлено",
            ai_findings="Легочные поля прозрачные, без очаговых и инфильтративных изменений. Корни легких структурны, не расширены.",
            ai_confidence=0.94,
            confirmation_status="pending",
        )
        result_3 = models.AnalysisResult(
            study_id=study_3.id,
            ai_status="needs_review",
            ai_diagnosis="Обнаружены патологические изменения. Необходимо дообследование",
            ai_findings="Выявлены очаговые изменения в легочной ткани. Рекомендуется проведение компьютерной томографии органов грудной клетки для уточнения характера изменений.",
            ai_confidence=0.55,
        )

        db.add_all([result_1, result_2, result_3])

        template = models.EmailTemplate(
            name="result_notification",
            subject="Результаты флюорографии — {patient_name}",
            body=(
                "Здравствуйте, {patient_name}!\n\n"
                "Ваше исследование от {taken_at} подтверждено врачом.\n"
                "Заключение: {findings}.\n\n"
                "Спасибо, что пользуетесь нашей клиникой."
            ),
        )
        db.add(template)

        try:
            db.commit()
            print(f"[DB] Демо-данные успешно загружены: {len([patient_1, patient_2, patient_3])} пациентов, {len([study_1, study_2, study_3])} исследований")
        except Exception as e:
            print(f"[DB] ОШИБКА при сохранении демо-данных: {e}")
            db.rollback()
            raise

