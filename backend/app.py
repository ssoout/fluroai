from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Query, APIRouter
from fastapi.routing import APIRoute
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import models
from backend.database import get_db, init_db, seed_demo_data
from backend.emailer import EmailMessage, EmailQueue
from backend.ml_service import analyze_image
from backend.schemas import (
    AlertItem,
    AnalysisConfirmRequest,
    AnalysisResultCreate,
    AnalysisResultDetail,
    AnalysisResultRead,
    DashboardAlertsResponse,
    DashboardRecentResponse,
    DashboardStats,
    PatientCreate,
    PatientRead,
    PatientUpdate,
    PendingResultItem,
    PendingResultsResponse,
    StudyCreate,
    StudyRead,
    StudyUpdate,
)

app = FastAPI(title="FluoroDesk Backend", version="0.2.0")
print('=== ЭТО ТОТ САМЫЙ app.py ===')

# Создаем отдельный router для маршрута studies, чтобы гарантировать порядок
patients_router = APIRouter(prefix="/patients", tags=["patients"])

# ЯВНАЯ ПРОВЕРКА РЕГИСТРАЦИИ МАРШРУТОВ
def _verify_routes():
    """Проверка регистрации маршрутов после загрузки модуля"""
    routes = [r.path for r in app.routes if hasattr(r, 'path')]
    patient_studies_route = '/patients/{patient_id}/studies'
    if patient_studies_route in routes:
        print(f'✓✓✓ МАРШРУТ {patient_studies_route} ЗАРЕГИСТРИРОВАН В APP!')
    else:
        print(f'✗✗✗ МАРШРУТ {patient_studies_route} НЕ НАЙДЕН!')
        print(f'Доступные маршруты patients: {[r for r in routes if "patients" in r]}')

@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    # НЕ удаляем данные при каждом запуске - используем force=False
    # Если нужно загрузить демо-данные только при первом запуске, используйте force=False
    seed_demo_data(force=False)
    if not hasattr(app.state, "email_queue"):
        app.state.email_queue = EmailQueue()
    await app.state.email_queue.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if hasattr(app.state, "email_queue"):
        await app.state.email_queue.stop()


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Patients CRUD
# КРИТИЧЕСКИ ВАЖНО: Более специфичные маршруты ДОЛЖНЫ быть ПЕРЕД более общими!
# /patients/{patient_id}/studies ДОЛЖЕН быть ПЕРВЫМ среди всех маршрутов patients!

# КРИТИЧЕСКИ ВАЖНО: Этот маршрут ДОЛЖЕН быть ПЕРВЫМ!
# Используем отдельный router для гарантии правильного порядка
@patients_router.get(
    "/{patient_id}/studies",
    response_model=List[StudyRead],
    summary="Получить все исследования пациента",
    description="Возвращает список всех исследований для указанного пациента",
    name="get_patient_studies"
)
def get_patient_studies(patient_id: int, db: Session = Depends(get_db)) -> List[StudyRead]:
    """Получить все исследования пациента."""
    print(f"[API] ===== ЗАПРОС ИССЛЕДОВАНИЙ ПАЦИЕНТА =====")
    print(f"[API] Patient ID: {patient_id}")
    
    # Проверяем существование пациента
    patient = db.get(models.Patient, patient_id)
    if not patient:
        print(f"[API] ✗ ОШИБКА: Пациент с ID={patient_id} не найден")
        raise HTTPException(status_code=404, detail="Patient not found")
    
    print(f"[API] ✓ Пациент найден: ID={patient.id}, Имя={patient.full_name}")
    
    # Получаем все исследования пациента
    studies = db.query(models.Study).filter(
        models.Study.patient_id == patient_id
    ).order_by(models.Study.taken_at.desc()).all()
    
    print(f"[API] Найдено исследований для пациента ID={patient_id}: {len(studies)}")
    
    # Дополнительная диагностика - показываем все исследования в БД
    all_studies = db.query(models.Study).all()
    print(f"[API] Всего исследований в БД: {len(all_studies)}")
    for s in all_studies:
        print(f"[API]   - Исследование ID={s.id}, Patient ID={s.patient_id}, Дата={s.taken_at}")
    
    # Показываем найденные исследования
    for study in studies:
        print(f"[API]   ✓ Исследование пациента: ID={study.id}, Patient ID={study.patient_id}, Дата={study.taken_at}, Image={study.image_path or 'нет'}")
    
    print(f"[API] Возвращаем {len(studies)} исследований")
    print(f"[API] ===== ЗАПРОС ЗАВЕРШЕН =====")
    return studies

# ВАЖНО: Включаем router ПЕРЕД всеми остальными маршрутами patients
app.include_router(patients_router)

@app.get("/patients", response_model=List[PatientRead], tags=["patients"])
def list_patients(db: Session = Depends(get_db)) -> List[PatientRead]:
    return db.query(models.Patient).order_by(models.Patient.created_at.desc()).all()


@app.post("/patients", response_model=PatientRead, tags=["patients"])
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)) -> PatientRead:
    try:
        print(f"[API] ===== СОЗДАНИЕ ПАЦИЕНТА =====")
        print(f"[API] Данные: Имя={payload.full_name}, Email={payload.email}, Birth Date={payload.birth_date}, MRN={payload.medical_record_number}")
        
        # Проверяем, какая БД используется
        from backend.database import DATABASE_URL
        db_type = "PostgreSQL" if DATABASE_URL.startswith("postgresql") else "SQLite"
        print(f"[API] Используется БД: {db_type}")
        if DATABASE_URL.startswith("postgresql"):
            db_info = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
            print(f"[API] PostgreSQL подключение: {db_info}")
        else:
            print(f"[API] SQLite файл: {DATABASE_URL}")
        
        patient = models.Patient(**payload.dict())
        db.add(patient)
        db.flush()  # Получаем ID до commit
        print(f"[API] Пациент добавлен в сессию: ID={patient.id}")
        
        db.commit()
        print(f"[API] ✓ Транзакция закоммичена")
        
        db.refresh(patient)
        print(f"[API] ✓ Пациент обновлен из БД: ID={patient.id}, Имя={patient.full_name}, Дата рождения={patient.birth_date}")
        
        # Проверяем, что пациент действительно сохранен
        saved_patient = db.get(models.Patient, patient.id)
        if saved_patient:
            print(f"[API] ✓ ПРОВЕРКА: Пациент найден в БД после сохранения: ID={saved_patient.id}, Имя={saved_patient.full_name}")
        else:
            print(f"[API] ✗ ОШИБКА: Пациент НЕ найден в БД после сохранения!")
        
        # Дополнительная проверка - считаем всех пациентов
        total_patients = db.query(models.Patient).count()
        print(f"[API] Всего пациентов в БД: {total_patients}")
        
        print(f"[API] ===== ПАЦИЕНТ СОЗДАН УСПЕШНО =====")
        return patient
    except Exception as e:
        print(f"[API] ✗✗✗ ОШИБКА при создании пациента: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании пациента: {str(e)}")


@app.get("/patients/{patient_id}", response_model=PatientRead, tags=["patients"])
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> PatientRead:
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.put("/patients/{patient_id}", response_model=PatientRead, tags=["patients"])
def update_patient(
    patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)
) -> PatientRead:
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for field, value in payload.dict().items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


@app.delete("/patients/{patient_id}", tags=["patients"])
def delete_patient(patient_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    patient = db.get(models.Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"status": "deleted"}

# ФИНАЛЬНАЯ ПРОВЕРКА И ПЕРЕУПОРЯДОЧИВАНИЕ МАРШРУТОВ
print("=" * 60)
print("ПРОВЕРКА РЕГИСТРАЦИИ МАРШРУТОВ PATIENTS:")
all_routes = [(r.path, list(r.methods) if hasattr(r, 'methods') else []) for r in app.routes if hasattr(r, 'path') and 'patients' in r.path]
for path, methods in sorted(all_routes):
    print(f"  {path} - {methods}")
if '/patients/{patient_id}/studies' in [r[0] for r in all_routes]:
    print("✓✓✓ МАРШРУТ /patients/{patient_id}/studies ЗАРЕГИСТРИРОВАН!")
    
    # ПЕРЕУПОРЯДОЧИВАНИЕ: Перемещаем маршрут studies в начало списка маршрутов
    # Это гарантирует, что он будет обработан первым
    studies_route = None
    other_routes = []
    for route in app.router.routes:
        if hasattr(route, 'path') and route.path == '/patients/{patient_id}/studies':
            studies_route = route
        elif hasattr(route, 'path') and 'patients' in route.path:
            other_routes.append(route)
    
    if studies_route:
        # Удаляем маршрут из текущей позиции
        app.router.routes.remove(studies_route)
        # Находим позицию первого маршрута patients и вставляем studies перед ним
        first_patient_idx = None
        for i, route in enumerate(app.router.routes):
            if hasattr(route, 'path') and 'patients' in route.path:
                first_patient_idx = i
                break
        if first_patient_idx is not None:
            app.router.routes.insert(first_patient_idx, studies_route)
            print("✓✓✓ МАРШРУТ /patients/{patient_id}/studies ПЕРЕМЕЩЕН В НАЧАЛО!")
        else:
            app.router.routes.insert(0, studies_route)
            print("✓✓✓ МАРШРУТ /patients/{patient_id}/studies ДОБАВЛЕН В НАЧАЛО!")
else:
    print("✗✗✗ МАРШРУТ /patients/{patient_id}/studies НЕ НАЙДЕН!")
print("=" * 60)

# ---------------------------------------------------------------------------
# Studies


@app.get("/studies", response_model=List[StudyRead], tags=["studies"])
def list_studies(
    patient_id: int | None = Query(None, description="Фильтр по ID пациента"),
    db: Session = Depends(get_db)
) -> List[StudyRead]:
    """Получить список исследований. Можно фильтровать по patient_id."""
    query = db.query(models.Study)
    if patient_id is not None:
        query = query.filter(models.Study.patient_id == patient_id)
    return query.order_by(models.Study.taken_at.desc()).all()


@app.get("/studies/{study_id}", response_model=StudyRead, tags=["studies"])
def get_study(study_id: int, db: Session = Depends(get_db)) -> StudyRead:
    study = db.get(models.Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return study


@app.post("/studies", response_model=StudyRead, tags=["studies"])
def create_study(payload: StudyCreate, db: Session = Depends(get_db)) -> StudyRead:
    try:
        print(f"[API] ===== СОЗДАНИЕ ИССЛЕДОВАНИЯ =====")
        print(f"[API] Patient ID из payload: {payload.patient_id}")
        print(f"[API] Данные: Дата={payload.taken_at}, Приоритет={payload.priority}")
        
        # Проверяем существование пациента
        patient = db.get(models.Patient, payload.patient_id)
        if not patient:
            print(f"[API] ✗ ОШИБКА: Пациент с ID={payload.patient_id} не найден")
            raise HTTPException(status_code=404, detail="Patient not found")
        
        print(f"[API] ✓ Пациент найден: ID={patient.id}, Имя={patient.full_name}")
        
        # Создаем исследование с явным указанием patient_id
        study_data = payload.dict()
        # Убеждаемся, что patient_id точно установлен
        study_data["patient_id"] = int(payload.patient_id)
        
        print(f"[API] Создание объекта Study с patient_id={study_data['patient_id']}")
        study = models.Study(**study_data)
        
        # Дополнительная проверка перед добавлением
        if study.patient_id != payload.patient_id:
            print(f"[API] ⚠ ВНИМАНИЕ: patient_id не совпадает! Устанавливаем явно.")
            study.patient_id = payload.patient_id
        
        print(f"[API] Исследование перед добавлением: Patient ID={study.patient_id}")
        
        db.add(study)
        db.flush()  # Получаем ID до commit
        print(f"[API] ✓ Исследование добавлено в сессию: ID={study.id}, Patient ID={study.patient_id}")
        
        # Коммитим транзакцию
        db.commit()
        print(f"[API] ✓ Транзакция закоммичена")
        
        # Обновляем объект из БД
        db.refresh(study)
        print(f"[API] ✓ Исследование обновлено из БД: ID={study.id}, Patient ID={study.patient_id}")
        
        # Проверяем, что исследование действительно сохранено
        saved_study = db.get(models.Study, study.id)
        if saved_study:
            print(f"[API] ✓ Исследование найдено в БД: ID={saved_study.id}, Patient ID={saved_study.patient_id}")
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА - запрашиваем все исследования пациента
            patient_studies = db.query(models.Study).filter(
                models.Study.patient_id == payload.patient_id
            ).order_by(models.Study.taken_at.desc()).all()
            
            print(f"[API] Всего исследований у пациента ID={payload.patient_id}: {len(patient_studies)}")
            for ps in patient_studies:
                print(f"[API]   - Исследование ID={ps.id}, Patient ID={ps.patient_id}, Дата={ps.taken_at}")
            
            # Проверяем, что наше исследование в списке
            found = any(s.id == saved_study.id for s in patient_studies)
            if found:
                print(f"[API] ✓✓✓ ИССЛЕДОВАНИЕ УСПЕШНО СВЯЗАНО С ПАЦИЕНТОМ!")
            else:
                print(f"[API] ✗✗✗ КРИТИЧЕСКАЯ ОШИБКА: Исследование не найдено в списке исследований пациента!")
                print(f"[API] Попытка восстановления связи...")
                # Пытаемся восстановить связь
                saved_study.patient_id = payload.patient_id
                db.commit()
                db.refresh(saved_study)
                print(f"[API] Связь восстановлена: Patient ID={saved_study.patient_id}")
        else:
            print(f"[API] ✗✗✗ КРИТИЧЕСКАЯ ОШИБКА: Исследование не найдено после сохранения!")
        
        print(f"[API] ===== ИССЛЕДОВАНИЕ СОЗДАНО =====")
        return study
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] ОШИБКА при создании исследования: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании исследования: {str(e)}")


@app.put("/studies/{study_id}", response_model=StudyRead, tags=["studies"])
def update_study(
    study_id: int, payload: StudyUpdate, db: Session = Depends(get_db)
) -> StudyRead:
    study = db.get(models.Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    for field, value in payload.dict(exclude_unset=True).items():
        if value is not None:
            setattr(study, field, value)
    db.commit()
    db.refresh(study)
    return study


@app.post("/studies/{study_id}/images", response_model=StudyRead, tags=["studies"])
async def upload_study_image(
    study_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> StudyRead:
    """Загрузка изображения для исследования и автоматический анализ."""
    try:
        print(f"[API] Начало загрузки изображения для исследования ID={study_id}")
        print(f"[API] Имя файла: {file.filename}, Content-Type: {file.content_type}")
        
        study = db.get(models.Study, study_id)
        if not study:
            print(f"[API] ОШИБКА: Исследование с ID={study_id} не найдено")
            raise HTTPException(status_code=404, detail="Study not found")
        
        print(f"[API] Исследование найдено: ID={study.id}, Patient ID={study.patient_id}")
        
        # Валидация формата
        allowed_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        if not file.filename:
            raise HTTPException(status_code=400, detail="Имя файла не указано")
        
        file_ext = Path(file.filename).suffix.lower()
        print(f"[API] Расширение файла: {file_ext}")
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(allowed_extensions)}"
            )
        
        # Создаем папку для загрузок
        uploads_dir = Path("uploads") / "studies" / str(study_id)
        try:
            uploads_dir.mkdir(parents=True, exist_ok=True)
            print(f"[API] Директория создана/проверена: {uploads_dir.absolute()}")
        except Exception as e:
            print(f"[API] ОШИБКА при создании директории: {e}")
            raise HTTPException(status_code=500, detail=f"Не удалось создать директорию для загрузки: {str(e)}")
        
        # Сохраняем файл
        file_path = uploads_dir / f"image{file_ext}"
        try:
            print(f"[API] Сохранение файла: {file_path.absolute()}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"[API] ✓ Файл успешно сохранен: {file_path.absolute()}")
            
            # Проверяем, что файл действительно создан
            if not file_path.exists():
                raise HTTPException(status_code=500, detail="Файл не был сохранен")
            print(f"[API] ✓ Файл существует, размер: {file_path.stat().st_size} байт")
        except Exception as e:
            print(f"[API] ОШИБКА при сохранении файла: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}")
        
        # Обновляем путь к изображению в базе
        try:
            # Сохраняем patient_id перед обновлением для проверки
            original_patient_id = study.patient_id
            print(f"[API] Обновление пути к изображению. Текущий Patient ID: {original_patient_id}")
            
            # Используем абсолютный путь для надежности
            study.image_path = str(file_path.absolute())
            print(f"[API] Обновление пути к изображению: {study.image_path}")
            
            # Убеждаемся, что patient_id не изменился
            if study.patient_id != original_patient_id:
                print(f"[API] ⚠ ВНИМАНИЕ: Patient ID изменился! Восстанавливаем: {original_patient_id}")
                study.patient_id = original_patient_id
            
            db.commit()
            db.refresh(study)
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА после commit - получаем свежие данные из БД
            fresh_study = db.get(models.Study, study_id)
            if fresh_study:
                if fresh_study.patient_id != original_patient_id:
                    print(f"[API] ✗✗✗ КРИТИЧЕСКАЯ ОШИБКА: Patient ID потерян! Было: {original_patient_id}, Стало: {fresh_study.patient_id}")
                    # Восстанавливаем
                    fresh_study.patient_id = original_patient_id
                    db.commit()
                    db.refresh(fresh_study)
                    print(f"[API] ✓ Связь восстановлена: Patient ID={fresh_study.patient_id}")
                else:
                    print(f"[API] ✓✓✓ Patient ID сохранен корректно: {fresh_study.patient_id}")
            else:
                print(f"[API] ✗ ОШИБКА: Исследование не найдено после commit!")
            
            print(f"[API] ✓ Исследование обновлено: ID={study.id}, Patient ID={study.patient_id}, Image Path={study.image_path}")
        except Exception as e:
            print(f"[API] ОШИБКА при обновлении исследования в БД: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ошибка при обновлении исследования: {str(e)}")
        
        # Автоматически запускаем анализ
        try:
            print(f"[API] Запуск анализа изображения: {file_path}")
            analysis_result = analyze_image(file_path)
            print(f"[API] ✓ Анализ завершен: статус={analysis_result.get('status')}, уверенность={analysis_result.get('confidence')}")
            
            # Создаем или обновляем результат анализа
            existing_result = (
                db.query(models.AnalysisResult)
                .filter(models.AnalysisResult.study_id == study_id)
                .first()
            )
            
            if existing_result:
                existing_result.ai_status = analysis_result["ai_status"]
                existing_result.ai_diagnosis = analysis_result.get("ai_diagnosis", "")
                existing_result.ai_findings = analysis_result["ai_findings"]
                existing_result.ai_confidence = analysis_result["ai_confidence"]
                existing_result.confirmation_status = "pending"
                db.commit()
                db.refresh(existing_result)
                print(f"[API] ✓ Результат анализа обновлен: ID={existing_result.id}")
            else:
                new_result = models.AnalysisResult(
                    study_id=study_id,
                    ai_status=analysis_result["ai_status"],
                    ai_diagnosis=analysis_result.get("ai_diagnosis", ""),
                    ai_findings=analysis_result["ai_findings"],
                    ai_confidence=analysis_result["ai_confidence"],
                    confirmation_status="pending",
                )
                db.add(new_result)
                db.commit()
                db.refresh(new_result)
                print(f"[API] ✓ Результат анализа сохранен: ID={new_result.id}")
        except Exception as e:
            # Если анализ не удался, все равно возвращаем исследование с загруженным изображением
            print(f"[API] ОШИБКА при анализе изображения: {e}")
            import traceback
            traceback.print_exc()
            try:
                db.rollback()
            except:
                pass
            # Продолжаем выполнение - изображение уже загружено
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] КРИТИЧЕСКАЯ ОШИБКА при загрузке изображения: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке изображения: {str(e)}")
    
    db.refresh(study)
    
    # ФИНАЛЬНАЯ КРИТИЧЕСКАЯ ПРОВЕРКА - убеждаемся, что patient_id не потерялся
    print(f"[API] ===== ФИНАЛЬНАЯ ПРОВЕРКА =====")
    final_check = db.get(models.Study, study_id)
    if final_check:
        print(f"[API] Исследование ID={final_check.id}, Patient ID={final_check.patient_id}, Image Path={final_check.image_path or 'нет'}")
        
        # Проверяем связь с пациентом
        if final_check.patient_id:
            patient_check = db.get(models.Patient, final_check.patient_id)
            if patient_check:
                print(f"[API] ✓ Пациент найден: ID={patient_check.id}, Имя={patient_check.full_name}")
                
                # Проверяем, что исследование в списке исследований пациента
                patient_studies_count = db.query(models.Study).filter(
                    models.Study.patient_id == final_check.patient_id
                ).count()
                print(f"[API] Всего исследований у этого пациента: {patient_studies_count}")
                
                # Проверяем, что наше исследование в списке
                found = db.query(models.Study).filter(
                    models.Study.id == study_id,
                    models.Study.patient_id == final_check.patient_id
                ).first()
                if found:
                    print(f"[API] ✓✓✓ ИССЛЕДОВАНИЕ УСПЕШНО СВЯЗАНО С ПАЦИЕНТОМ!")
                else:
                    print(f"[API] ✗✗✗ КРИТИЧЕСКАЯ ОШИБКА: Исследование не найдено в списке исследований пациента!")
            else:
                print(f"[API] ✗ ОШИБКА: Пациент с ID={final_check.patient_id} не найден!")
        else:
            print(f"[API] ✗✗✗ КРИТИЧЕСКАЯ ОШИБКА: Patient ID отсутствует!")
    else:
        print(f"[API] ✗✗✗ КРИТИЧЕСКАЯ ОШИБКА: Исследование не найдено после всех операций!")
    
    print(f"[API] ===== ЗАГРУЗКА ИЗОБРАЖЕНИЯ ЗАВЕРШЕНА =====")
    return study


@app.get("/studies/{study_id}/analysis", response_model=AnalysisResultRead, tags=["studies"])
def get_study_analysis(
    study_id: int,
    db: Session = Depends(get_db),
) -> AnalysisResultRead:
    """Получить результат анализа для исследования."""
    result = (
        db.query(models.AnalysisResult)
        .filter(models.AnalysisResult.study_id == study_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return result


@app.post("/studies/{study_id}/analyze", response_model=AnalysisResultRead, tags=["studies"])
def analyze_study_image(
    study_id: int,
    db: Session = Depends(get_db),
) -> AnalysisResultRead:
    """Запустить анализ изображения для исследования."""
    study = db.get(models.Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    if not study.image_path or not Path(study.image_path).exists():
        raise HTTPException(
            status_code=400,
            detail="Изображение не загружено для этого исследования"
        )
    
    try:
        analysis_result = analyze_image(study.image_path)
        
        # Создаем или обновляем результат анализа
        existing_result = (
            db.query(models.AnalysisResult)
            .filter(models.AnalysisResult.study_id == study_id)
            .first()
        )
        
        if existing_result:
            existing_result.ai_status = analysis_result["ai_status"]
            existing_result.ai_diagnosis = analysis_result.get("ai_diagnosis", "")
            existing_result.ai_findings = analysis_result["ai_findings"]
            existing_result.ai_confidence = analysis_result["ai_confidence"]
            existing_result.confirmation_status = "pending"
            db.commit()
            db.refresh(existing_result)
            return existing_result
        else:
            new_result = models.AnalysisResult(
                study_id=study_id,
                ai_status=analysis_result["ai_status"],
                ai_diagnosis=analysis_result.get("ai_diagnosis", ""),
                ai_findings=analysis_result["ai_findings"],
                ai_confidence=analysis_result["ai_confidence"],
                confirmation_status="pending",
            )
            db.add(new_result)
            db.commit()
            db.refresh(new_result)
            return new_result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при анализе изображения: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Analysis


@app.post("/analysis/run", response_model=AnalysisResultRead, tags=["analysis"])
def run_analysis(
    payload: AnalysisResultCreate,
    db: Session = Depends(get_db),
) -> AnalysisResultRead:
    study = db.get(models.Study, payload.study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    analysis = models.AnalysisResult(
        study_id=payload.study_id,
        ai_status=payload.ai_status,
        ai_findings=payload.ai_findings,
        ai_confidence=payload.ai_confidence,
        confirmation_status="pending",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@app.post(
    "/analysis/{result_id}/confirm",
    response_model=AnalysisResultRead,
    tags=["analysis"],
)
async def confirm_analysis_result(
    result_id: int,
    payload: AnalysisConfirmRequest,
    db: Session = Depends(get_db),
) -> AnalysisResultRead:
    result = (
        db.query(models.AnalysisResult)
        .join(models.Study, models.AnalysisResult.study)
        .join(models.Patient, models.Study.patient)
        .filter(models.AnalysisResult.id == result_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    result.confirmation_status = "approved" if payload.action == "approve" else "rejected"
    result.confirmation_notes = payload.notes
    result.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(result)

    if (
        payload.action == "approve"
        and hasattr(app.state, "email_queue")
        and result.study
        and result.study.patient
    ):
        template = (
            db.query(models.EmailTemplate)
            .filter(models.EmailTemplate.name == "result_notification")
            .first()
        )
        patient = result.study.patient
        subject = template.subject.format(patient_name=patient.full_name) if template else (
            f"Результаты флюорографии для {patient.full_name}"
        )
        body_template = template.body if template else (
            "Уважаемый(ая) {patient_name}, результат исследования: {findings}."
        )
        body = body_template.format(
            patient_name=patient.full_name,
            taken_at=result.study.taken_at.strftime("%Y-%m-%d %H:%M"),
            findings=result.ai_findings,
            diagnosis=result.ai_diagnosis or "Не указан",
        )
        message = EmailMessage(to=patient.email, subject=subject, body=body)
        await app.state.email_queue.enqueue(message)

    return result


@app.post(
    "/analysis/{result_id}/send-email",
    tags=["analysis"],
)
async def send_result_email(
    result_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Отправить результаты анализа на email пациента."""
    result = (
        db.query(models.AnalysisResult)
        .join(models.Study, models.AnalysisResult.study)
        .join(models.Patient, models.Study.patient)
        .filter(models.AnalysisResult.id == result_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if not result.study or not result.study.patient:
        raise HTTPException(status_code=400, detail="Patient information not found")
    
    patient = result.study.patient
    if not patient.email:
        raise HTTPException(status_code=400, detail="Patient email not found")
    
    # Получаем шаблон email
    template = (
        db.query(models.EmailTemplate)
        .filter(models.EmailTemplate.name == "result_notification")
        .first()
    )
    
    # Формируем тему и тело письма
    subject = template.subject.format(patient_name=patient.full_name) if template else (
        f"Результаты флюорографии для {patient.full_name}"
    )
    
    body_template = template.body if template else (
        "Уважаемый(ая) {patient_name}!\n\n"
        "Результаты вашего исследования от {taken_at}:\n\n"
        "Диагноз: {diagnosis}\n"
        "Описание: {findings}\n"
        "Уверенность анализа: {confidence}%\n\n"
        "С уважением,\n"
        "Медицинский центр"
    )
    
    status_map = {
        "clear": "Норма",
        "pathology_detected": "Патология обнаружена",
        "needs_review": "Требуется дополнительная проверка"
    }
    
    body = body_template.format(
        patient_name=patient.full_name,
        taken_at=result.study.taken_at.strftime("%d.%m.%Y %H:%M"),
        diagnosis=result.ai_diagnosis or "Не указан",
        findings=result.ai_findings or "Описание отсутствует",
        confidence=round((result.ai_confidence or 0) * 100, 1),
        status=status_map.get(result.ai_status, "Неизвестно"),
    )
    
    # Отправляем email
    if hasattr(app.state, "email_queue"):
        message = EmailMessage(to=patient.email, subject=subject, body=body)
        await app.state.email_queue.enqueue(message)
        return {"status": "sent", "message": f"Email отправлен на {patient.email}"}
    else:
        raise HTTPException(status_code=500, detail="Email queue not initialized")


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------


@app.get(
    "/analysis/pending",
    response_model=PendingResultsResponse,
    tags=["analysis"],
)
def list_pending_analysis(db: Session = Depends(get_db)) -> PendingResultsResponse:
    results = (
        db.query(models.AnalysisResult, models.Study, models.Patient)
        .join(models.Study, models.AnalysisResult.study)
        .join(models.Patient, models.Study.patient)
        .filter(
            (models.AnalysisResult.ai_confidence.is_(None))
            | (models.AnalysisResult.ai_confidence < 0.7)
            | (models.AnalysisResult.confirmation_status != "approved")
        )
        .order_by(models.AnalysisResult.created_at.desc())
        .all()
    )

    items = [
        PendingResultItem(
            result_id=row.AnalysisResult.id,
            patient_name=row.Patient.full_name,
            taken_at=row.Study.taken_at,
            ai_status=row.AnalysisResult.ai_status,
            ai_findings=row.AnalysisResult.ai_findings,
            ai_confidence=row.AnalysisResult.ai_confidence,
            confirmation_status=row.AnalysisResult.confirmation_status,
        )
        for row in results
    ]
    return PendingResultsResponse(items=items)


@app.get(
    "/analysis/{result_id}",
    response_model=AnalysisResultDetail,
    tags=["analysis"],
)
def get_analysis_detail(
    result_id: int, db: Session = Depends(get_db)
) -> AnalysisResultDetail:
    result = (
        db.query(models.AnalysisResult)
        .join(models.Study, models.AnalysisResult.study)
        .join(models.Patient, models.Study.patient)
        .filter(models.AnalysisResult.id == result_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    return AnalysisResultDetail(
        result=AnalysisResultRead.from_orm(result),
        study=StudyRead.from_orm(result.study),
        patient=PatientRead.from_orm(result.study.patient),
    )


# ---------------------------------------------------------------------------
# Dashboard


def _needs_manual_review(result: models.AnalysisResult) -> bool:
    return (
        result.ai_confidence is None
        or result.ai_confidence < 0.7
        or result.confirmation_status != "approved"
    )


@app.get("/dashboard/recent", response_model=DashboardRecentResponse, tags=["dashboard"])
def get_recent_results(db: Session = Depends(get_db)) -> DashboardRecentResponse:
    results = (
        db.query(models.AnalysisResult, models.Study, models.Patient)
        .join(models.Study, models.AnalysisResult.study)
        .join(models.Patient, models.Study.patient)
        .order_by(models.AnalysisResult.created_at.desc())
        .limit(20)
        .all()
    )
    items = [
        {
            "result_id": result.AnalysisResult.id,
            "patient_name": result.Patient.full_name,
            "taken_at": result.Study.taken_at,
            "status": result.AnalysisResult.ai_status,
            "findings": result.AnalysisResult.ai_findings,
            "confidence": result.AnalysisResult.ai_confidence,
            "confirmation_status": result.AnalysisResult.confirmation_status,
            "needs_manual_review": _needs_manual_review(result.AnalysisResult),
        }
        for result in results
    ]
    return DashboardRecentResponse(items=items)


@app.get("/dashboard/stats", response_model=DashboardStats, tags=["dashboard"])
def get_stats(db: Session = Depends(get_db)) -> DashboardStats:
    processed = db.query(func.count(models.AnalysisResult.id)).scalar() or 0
    pathology_count = (
        db.query(func.count(models.AnalysisResult.id))
        .filter(models.AnalysisResult.ai_status == "pathology_detected")
        .scalar()
        or 0
    )
    manual_review = (
        db.query(func.count(models.AnalysisResult.id))
        .filter(models.AnalysisResult.confirmation_status != "approved")
        .scalar()
        or 0
    )
    return DashboardStats(
        processed=processed,
        pathology_count=pathology_count,
        manual_review=manual_review,
    )


@app.get("/dashboard/alerts", response_model=DashboardAlertsResponse, tags=["dashboard"])
def get_alerts(db: Session = Depends(get_db)) -> DashboardAlertsResponse:
    results = (
        db.query(models.AnalysisResult, models.Study, models.Patient)
        .join(models.Study, models.AnalysisResult.study)
        .join(models.Patient, models.Study.patient)
        .filter(
            (models.AnalysisResult.ai_confidence.is_(None))
            | (models.AnalysisResult.ai_confidence < 0.7)
            | (models.AnalysisResult.confirmation_status != "approved")
        )
        .order_by(models.AnalysisResult.created_at.desc())
        .limit(10)
        .all()
    )

    items = [
        AlertItem(
            result_id=result.AnalysisResult.id,
            patient_name=result.Patient.full_name,
            taken_at=result.Study.taken_at,
            reason="Низкая уверенность анализа, требуется ручная проверка"
            if (result.AnalysisResult.ai_confidence or 0) < 0.7
            else "Ожидает подтверждения врача",
            resolved=result.AnalysisResult.confirmation_status == "approved",
        )
        for result in results
    ]
    return DashboardAlertsResponse(items=items)

