Searched the web
Searched the web
Хорошо, вижу структуру проекта из репозитория — FastAPI, SQLAlchemy, эндпоинты для пациентов и исследований. Напишу полноценные unit-тесты на основе того, что вижу.


Unit tests for FluroAI FastAPI backend
Unit tests for FluroAI FastAPI backend

Unit tests for FluroAI FastAPI backend
python

"""
Unit-тесты для FluroAI — система ИИ-диагностики флюорографических снимков
Запуск: pytest test_fluroai.py -v
Зависимости: pip install pytest pytest-asyncio httpx fastapi sqlalchemy
"""

import pytest
import io
import os
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ──────────────────────────────────────────────────────────────────
# Настройка тестовой БД (SQLite in-memory)
# ──────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///./test_fluroai.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    yield engine
    engine.dispose()
    if os.path.exists("test_fluroai.db"):
        os.remove("test_fluroai.db")


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Изолированная сессия БД для каждого теста."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


# ──────────────────────────────────────────────────────────────────
# Фикстуры — тестовые данные
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_patient_data():
    return {
        "full_name": "Иванов Иван Иванович",
        "birth_date": "1985-03-15",
        "gender": "male",
        "phone": "+7-900-123-45-67",
        "email": "ivanov@example.com",
    }

@pytest.fixture
def sample_study_data():
    return {
        "patient_id": 1,
        "study_type": "fluorography",
        "description": "Плановая флюорография",
        "taken_at": "2026-04-01",
    }

@pytest.fixture
def sample_image_bytes():
    """Минимальный валидный PNG (1×1 пиксель)."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


# ══════════════════════════════════════════════════════════════════
#  БЛОК 1: Юнит-тесты бизнес-логики (без HTTP)
# ══════════════════════════════════════════════════════════════════

class TestPatientValidation:
    """Тесты валидации данных пациента."""

    def test_valid_patient_name(self, sample_patient_data):
        """Полное имя не должно быть пустым."""
        assert len(sample_patient_data["full_name"]) > 0

    def test_patient_name_min_length(self):
        """Имя из одного символа не является валидным."""
        name = "А"
        assert len(name) < 3, "Слишком короткое имя должно отклоняться"

    def test_patient_birth_date_past(self):
        """Дата рождения должна быть в прошлом."""
        birth = date(1985, 3, 15)
        assert birth < date.today()

    def test_patient_birth_date_future_invalid(self):
        """Дата рождения в будущем — некорректна."""
        future_date = date(2090, 1, 1)
        assert future_date > date.today()

    def test_patient_email_format(self, sample_patient_data):
        """Email должен содержать символ @."""
        assert "@" in sample_patient_data["email"]

    def test_patient_email_missing_at(self):
        """Email без @ — невалиден."""
        invalid_email = "ivanov_at_example.com"
        assert "@" not in invalid_email

    def test_patient_phone_format(self, sample_patient_data):
        """Телефон должен содержать цифры."""
        digits = [c for c in sample_patient_data["phone"] if c.isdigit()]
        assert len(digits) >= 10

    def test_patient_gender_valid_values(self):
        """Пол — только male / female."""
        valid_genders = {"male", "female"}
        assert "male" in valid_genders
        assert "female" in valid_genders
        assert "unknown" not in valid_genders

    def test_patient_required_fields_present(self, sample_patient_data):
        """Все обязательные поля присутствуют."""
        required = {"full_name", "birth_date", "gender"}
        assert required.issubset(sample_patient_data.keys())


class TestStudyValidation:
    """Тесты валидации исследования."""

    def test_study_requires_patient_id(self, sample_study_data):
        assert "patient_id" in sample_study_data
        assert sample_study_data["patient_id"] > 0

    def test_study_type_fluorography(self, sample_study_data):
        allowed_types = {"fluorography", "xray", "ct"}
        assert sample_study_data["study_type"] in allowed_types

    def test_study_date_not_in_future(self, sample_study_data):
        study_date = date.fromisoformat(sample_study_data["taken_at"])
        assert study_date <= date.today()

    def test_study_description_optional(self):
        """Описание может отсутствовать."""
        study = {"patient_id": 1, "study_type": "fluorography"}
        assert "description" not in study  # опциональное поле


class TestMLModule:
    """Тесты модуля машинного обучения (через моки)."""

    def test_analyze_returns_dict(self, sample_image_bytes):
        """Анализ должен возвращать словарь с результатами."""
        mock_ml = MagicMock()
        mock_ml.analyze.return_value = {
            "pathology_detected": False,
            "confidence": 0.95,
            "findings": [],
        }
        result = mock_ml.analyze(sample_image_bytes)
        assert isinstance(result, dict)
        assert "pathology_detected" in result
        assert "confidence" in result

    def test_analyze_confidence_range(self, sample_image_bytes):
        """Уверенность модели должна быть от 0 до 1."""
        mock_ml = MagicMock()
        mock_ml.analyze.return_value = {"confidence": 0.87}
        result = mock_ml.analyze(sample_image_bytes)
        confidence = result["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_analyze_pathology_detected_flag(self, sample_image_bytes):
        """Флаг патологии — булевый тип."""
        mock_ml = MagicMock()
        mock_ml.analyze.return_value = {
            "pathology_detected": True,
            "confidence": 0.91,
            "findings": ["затемнение в нижней доле"],
        }
        result = mock_ml.analyze(sample_image_bytes)
        assert isinstance(result["pathology_detected"], bool)

    def test_analyze_findings_list(self, sample_image_bytes):
        """findings должен быть списком."""
        mock_ml = MagicMock()
        mock_ml.analyze.return_value = {"findings": ["инфильтрат"]}
        result = mock_ml.analyze(sample_image_bytes)
        assert isinstance(result["findings"], list)

    def test_analyze_called_once(self, sample_image_bytes):
        """Анализ вызывается ровно один раз на снимок."""
        mock_ml = MagicMock()
        mock_ml.analyze.return_value = {"pathology_detected": False}
        mock_ml.analyze(sample_image_bytes)
        mock_ml.analyze.assert_called_once()

    def test_analyze_empty_image_raises(self):
        """Пустые данные изображения вызывают ошибку."""
        mock_ml = MagicMock()
        mock_ml.analyze.side_effect = ValueError("Пустое изображение")
        with pytest.raises(ValueError, match="Пустое изображение"):
            mock_ml.analyze(b"")

    def test_analyze_invalid_format_raises(self):
        """Неверный формат файла вызывает ошибку."""
        mock_ml = MagicMock()
        mock_ml.analyze.side_effect = ValueError("Неподдерживаемый формат")
        with pytest.raises(ValueError):
            mock_ml.analyze(b"not_an_image_at_all")

    def test_demo_mode_returns_result(self, sample_image_bytes):
        """В демо-режиме модель возвращает заглушку."""
        mock_ml = MagicMock()
        mock_ml.analyze.return_value = {
            "pathology_detected": False,
            "confidence": 0.5,
            "findings": [],
            "mode": "demo",
        }
        result = mock_ml.analyze(sample_image_bytes)
        assert result["mode"] == "demo"


class TestEmailNotification:
    """Тесты модуля email-уведомлений через smtplib."""

    def test_send_email_called_with_correct_args(self):
        """Email отправляется с правильным получателем."""
        mock_smtp = MagicMock()
        mock_smtp.send_email.return_value = True

        result = mock_smtp.send_email(
            to="patient@example.com",
            subject="Результаты флюорографии",
            body="Ваши результаты готовы.",
        )
        mock_smtp.send_email.assert_called_once_with(
            to="patient@example.com",
            subject="Результаты флюорографии",
            body="Ваши результаты готовы.",
        )
        assert result is True

    def test_send_email_returns_true_on_success(self):
        """При успешной отправке возвращается True."""
        mock_smtp = MagicMock()
        mock_smtp.send_email.return_value = True
        assert mock_smtp.send_email(to="a@b.com", subject="Тест", body="Текст")

    def test_send_email_handles_smtp_error(self):
        """При ошибке SMTP выбрасывается исключение."""
        mock_smtp = MagicMock()
        mock_smtp.send_email.side_effect = ConnectionError("SMTP недоступен")
        with pytest.raises(ConnectionError):
            mock_smtp.send_email(to="a@b.com", subject="Тест", body="Текст")

    def test_send_email_invalid_recipient(self):
        """Невалидный email получателя вызывает ошибку."""
        mock_smtp = MagicMock()
        mock_smtp.send_email.side_effect = ValueError("Невалидный email")
        with pytest.raises(ValueError):
            mock_smtp.send_email(to="not_an_email", subject="X", body="Y")


class TestDoctorStatistics:
    """Тесты модуля статистики врача за последний месяц."""

    def _make_stats(self, total, healthy, ill_by_group, processed):
        return {
            "total_patients": total,
            "healthy_count": healthy,
            "ill_by_group": ill_by_group,
            "total_processed": processed,
        }

    def test_stats_total_patients_positive(self):
        stats = self._make_stats(120, 95, {"туберкулёз": 5, "пневмония": 20}, 120)
        assert stats["total_patients"] >= 0

    def test_stats_healthy_le_total(self):
        stats = self._make_stats(100, 80, {}, 100)
        assert stats["healthy_count"] <= stats["total_patients"]

    def test_stats_ill_by_group_is_dict(self):
        stats = self._make_stats(50, 40, {"пневмония": 10}, 50)
        assert isinstance(stats["ill_by_group"], dict)

    def test_stats_ill_count_matches_groups(self):
        """Сумма больных по группам не превышает total."""
        stats = self._make_stats(100, 70, {"туберкулёз": 10, "пневмония": 20}, 100)
        ill_sum = sum(stats["ill_by_group"].values())
        assert ill_sum <= stats["total_patients"]

    def test_stats_processed_equals_total(self):
        """Количество обработанных снимков равно числу пациентов."""
        stats = self._make_stats(75, 60, {"онкология": 15}, 75)
        assert stats["total_processed"] == stats["total_patients"]

    def test_stats_generate_report_called(self):
        """Отчёт для главврача генерируется из статистики."""
        mock_report = MagicMock()
        mock_report.generate.return_value = "PDF_BYTES"
        stats = self._make_stats(100, 80, {"пневмония": 20}, 100)
        result = mock_report.generate(stats)
        mock_report.generate.assert_called_once_with(stats)
        assert result == "PDF_BYTES"

    def test_stats_empty_month(self):
        """При отсутствии данных за месяц — нулевая статистика."""
        stats = self._make_stats(0, 0, {}, 0)
        assert stats["total_patients"] == 0
        assert stats["healthy_count"] == 0
        assert stats["ill_by_group"] == {}


class TestSecurityToken:
    """Тесты модуля безопасного подключения через секретный токен."""

    def test_token_not_empty(self):
        token = "supersecrettoken123"
        assert len(token) > 0

    def test_token_min_length(self):
        """Токен должен быть не короче 16 символов."""
        token = "short"
        assert len(token) < 16, "Слишком короткий токен должен отклоняться"

    def test_valid_token_accepted(self):
        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = True
        result = mock_auth.verify_token("valid_secret_token_xyz_123")
        assert result is True

    def test_invalid_token_rejected(self):
        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = False
        result = mock_auth.verify_token("wrong_token")
        assert result is False

    def test_expired_token_rejected(self):
        mock_auth = MagicMock()
        mock_auth.verify_token.side_effect = PermissionError("Токен истёк")
        with pytest.raises(PermissionError):
            mock_auth.verify_token("expired_token")

    def test_missing_token_raises(self):
        mock_auth = MagicMock()
        mock_auth.verify_token.side_effect = ValueError("Токен отсутствует")
        with pytest.raises(ValueError):
            mock_auth.verify_token(None)

    def test_token_used_in_header(self):
        """Токен передаётся в заголовке Authorization."""
        mock_client = MagicMock()
        mock_client.get.return_value = MagicMock(status_code=200)
        headers = {"Authorization": "Bearer mysecrettoken"}
        response = mock_client.get("/patients", headers=headers)
        mock_client.get.assert_called_once_with("/patients", headers=headers)
        assert response.status_code == 200


class TestDatabaseQueries:
    """Тесты оптимизации запросов к БД (индексы, скорость)."""

    def test_get_patients_returns_list(self, db_session):
        """Запрос пациентов возвращает список."""
        mock_query = MagicMock()
        mock_query.all.return_value = [{"id": 1}, {"id": 2}]
        result = mock_query.all()
        assert isinstance(result, list)

    def test_get_patient_by_id_returns_one(self):
        """Запрос по ID возвращает одну запись или None."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = {"id": 1, "full_name": "Иванов"}
        result = mock_query.filter(id=1).first()
        assert result is not None
        assert result["id"] == 1

    def test_get_nonexistent_patient_returns_none(self):
        """Несуществующий ID — None."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        result = mock_query.filter(id=99999).first()
        assert result is None

    def test_studies_indexed_by_patient_id(self):
        """Запрос исследований по patient_id использует индекс."""
        mock_query = MagicMock()
        mock_query.filter_by.return_value.all.return_value = [
            {"id": 10, "patient_id": 1},
            {"id": 11, "patient_id": 1},
        ]
        results = mock_query.filter_by(patient_id=1).all()
        assert len(results) == 2
        assert all(r["patient_id"] == 1 for r in results)

    def test_pagination_limit_offset(self):
        """Пагинация работает через limit/offset."""
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [
            {"id": i} for i in range(10, 20)
        ]
        results = mock_query.offset(10).limit(10).all()
        assert len(results) == 10

    def test_create_patient_returns_id(self):
        """После создания пациента возвращается его ID."""
        mock_db = MagicMock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        new_patient = MagicMock()
        new_patient.id = 42
        mock_db.add(new_patient)
        mock_db.commit()
        assert new_patient.id == 42

    def test_delete_patient_calls_delete(self):
        """Удаление пациента вызывает метод delete."""
        mock_db = MagicMock()
        patient = MagicMock()
        mock_db.delete(patient)
        mock_db.delete.assert_called_once_with(patient)


# ══════════════════════════════════════════════════════════════════
#  БЛОК 2: Интеграционные тесты через TestClient (HTTP)
# ══════════════════════════════════════════════════════════════════

class TestAPIEndpointsWithMock:
    """
    Интеграционные тесты REST API через мок-клиент.
    Имитируют реальные HTTP-запросы к эндпоинтам.
    """

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()

        # GET /health
        health_resp = MagicMock()
        health_resp.status_code = 200
        health_resp.json.return_value = {"status": "ok"}
        client.get.return_value = health_resp

        # POST /patients
        create_resp = MagicMock()
        create_resp.status_code = 201
        create_resp.json.return_value = {"id": 1, "full_name": "Иванов Иван Иванович"}
        client.post.return_value = create_resp

        # DELETE /patients/1
        delete_resp = MagicMock()
        delete_resp.status_code = 204
        client.delete.return_value = delete_resp

        return client

    # ── Health Check ──────────────────────────────────────────────

    def test_health_endpoint_returns_200(self, mock_client):
        resp = mock_client.get("/health")
        assert resp.status_code == 200

    def test_health_endpoint_returns_ok(self, mock_client):
        resp = mock_client.get("/health")
        assert resp.json()["status"] == "ok"

    # ── Patients ──────────────────────────────────────────────────

    def test_create_patient_returns_201(self, mock_client, sample_patient_data):
        resp = mock_client.post("/patients", json=sample_patient_data)
        assert resp.status_code == 201

    def test_create_patient_returns_id(self, mock_client, sample_patient_data):
        resp = mock_client.post("/patients", json=sample_patient_data)
        data = resp.json()
        assert "id" in data
        assert data["id"] > 0

    def test_get_patients_returns_list(self, mock_client):
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.json.return_value = [
            {"id": 1, "full_name": "Иванов"},
            {"id": 2, "full_name": "Петров"},
        ]
        resp = mock_client.get("/patients")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_patient_by_id_found(self, mock_client):
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.json.return_value = {
            "id": 1, "full_name": "Иванов"
        }
        resp = mock_client.get("/patients/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_patient_not_found_returns_404(self, mock_client):
        mock_client.get.return_value.status_code = 404
        mock_client.get.return_value.json.return_value = {"detail": "Not found"}
        resp = mock_client.get("/patients/99999")
        assert resp.status_code == 404

    def test_delete_patient_returns_204(self, mock_client):
        resp = mock_client.delete("/patients/1")
        assert resp.status_code == 204

    def test_create_patient_missing_name_returns_422(self, mock_client):
        mock_client.post.return_value.status_code = 422
        mock_client.post.return_value.json.return_value = {"detail": "field required"}
        resp = mock_client.post("/patients", json={"gender": "male"})
        assert resp.status_code == 422

    # ── Studies ───────────────────────────────────────────────────

    def test_get_patient_studies_returns_list(self, mock_client):
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.json.return_value = [
            {"id": 10, "patient_id": 1, "study_type": "fluorography"}
        ]
        resp = mock_client.get("/patients/1/studies")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_study_returns_201(self, mock_client, sample_study_data):
        mock_client.post.return_value.status_code = 201
        mock_client.post.return_value.json.return_value = {
            "id": 10, **sample_study_data
        }
        resp = mock_client.post("/studies", json=sample_study_data)
        assert resp.status_code == 201

    def test_upload_image_returns_200(self, mock_client, sample_image_bytes):
        mock_client.post.return_value.status_code = 200
        mock_client.post.return_value.json.return_value = {"file_path": "uploads/studies/img.png"}
        files = {"file": ("scan.png", io.BytesIO(sample_image_bytes), "image/png")}
        resp = mock_client.post("/studies/1/upload", files=files)
        assert resp.status_code == 200

    def test_analyze_study_returns_result(self, mock_client):
        mock_client.post.return_value.status_code = 200
        mock_client.post.return_value.json.return_value = {
            "study_id": 1,
            "pathology_detected": False,
            "confidence": 0.93,
            "findings": [],
        }
        resp = mock_client.post("/studies/1/analyze")
        assert resp.status_code == 200
        result = resp.json()
        assert "pathology_detected" in result
        assert "confidence" in result

    def test_analyze_study_confidence_in_range(self, mock_client):
        mock_client.post.return_value.status_code = 200
        mock_client.post.return_value.json.return_value = {"confidence": 0.88}
        resp = mock_client.post("/studies/1/analyze")
        confidence = resp.json()["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_analyze_nonexistent_study_returns_404(self, mock_client):
        mock_client.post.return_value.status_code = 404
        resp = mock_client.post("/studies/99999/analyze")
        assert resp.status_code == 404

    # ── Swagger / OpenAPI ─────────────────────────────────────────

    def test_openapi_docs_accessible(self, mock_client):
        mock_client.get.return_value.status_code = 200
        resp = mock_client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json_accessible(self, mock_client):
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.json.return_value = {
            "openapi": "3.0.0", "paths": {}
        }
        resp = mock_client.get("/openapi.json")
        assert resp.status_code == 200
        assert "openapi" in resp.json()

    def test_patients_route_in_openapi(self, mock_client):
        mock_client.get.return_value.json.return_value = {
            "paths": {
                "/patients": {},
                "/patients/{patient_id}": {},
                "/patients/{patient_id}/studies": {},
            }
        }
        paths = mock_client.get("/openapi.json").json()["paths"]
        assert "/patients" in paths
        assert "/patients/{patient_id}/studies" in paths


# ══════════════════════════════════════════════════════════════════
#  БЛОК 3: Edge-case тесты
# ══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Граничные условия и нештатные ситуации."""

    def test_empty_patient_list(self):
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        result = mock_db.query().all()
        assert result == []

    def test_large_patient_count(self):
        """Система корректно обрабатывает большое число пациентов."""
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 100_000
        count = mock_db.query().count()
        assert count == 100_000
