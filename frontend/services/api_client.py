from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class ApiError(Exception):
    """Ошибка, возникающая при обращении к backend API."""


@dataclass
class ApiClient:
    """Простой HTTP‑клиент для взаимодействия с FastAPI backend."""

    base_url: str = ""
    timeout: int = 10

    def __post_init__(self) -> None:
        if not self.base_url:
            self.base_url = os.getenv("FLURO_BACKEND_URL", "http://127.0.0.1:8000")
        self.base_url = self.base_url.rstrip("/")

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #
    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def get_dashboard_stats(self) -> Dict[str, Any]:
        return self._request("GET", "/dashboard/stats")

    def get_dashboard_recent(self) -> Dict[str, Any]:
        return self._request("GET", "/dashboard/recent")

    def get_dashboard_alerts(self) -> Dict[str, Any]:
        return self._request("GET", "/dashboard/alerts")

    def list_patients(self) -> list[Dict[str, Any]]:
        return self._request("GET", "/patients")
    
    def get_patient(self, patient_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/patients/{patient_id}")
    
    def create_patient(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Создать нового пациента."""
        return self._request("POST", "/patients", json=payload)
    
    def get_patient_studies(self, patient_id: int) -> list[Dict[str, Any]]:
        """Получить все исследования пациента."""
        try:
            print(f"[API_CLIENT] Запрос исследований для пациента ID={patient_id}")
            result = self._request("GET", f"/patients/{patient_id}/studies")
            print(f"[API_CLIENT] Получен ответ: тип={type(result)}, длина={len(result) if isinstance(result, list) else 'N/A'}")
            
            # Убеждаемся, что возвращается список
            if isinstance(result, list):
                print(f"[API_CLIENT] Возвращаем список из {len(result)} исследований")
                return result
            # Если backend вернул пустой словарь (пустой ответ), возвращаем пустой список
            if isinstance(result, dict) and not result:
                print(f"[API_CLIENT] Получен пустой словарь, возвращаем пустой список")
                return []
            # Если backend вернул что-то другое, возвращаем пустой список
            print(f"[API_CLIENT] Неожиданный тип ответа: {type(result)}, возвращаем пустой список")
            return []
        except ApiError as e:
            print(f"[API_CLIENT] ОШИБКА API: {e}")
            # Если пациент не найден (404), возвращаем пустой список
            if "404" in str(e) or "not found" in str(e).lower():
                return []
            # Иначе пробрасываем ошибку дальше
            raise

    def create_study(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/studies", json=payload)

    def update_study(self, study_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/studies/{study_id}", json=payload)

    def upload_study_image(self, study_id: int, file_path: str) -> Dict[str, Any]:
        """Загрузить изображение для исследования."""
        import os
        from pathlib import Path
        
        file_ext = Path(file_path).suffix.lower()
        content_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff"
        }
        content_type = content_type_map.get(file_ext, "image/png")
        
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, content_type)}
            # Используем requests напрямую для multipart/form-data
            url = f"{self.base_url}/studies/{study_id}/images"
            response = requests.post(url, files=files, timeout=self.timeout * 3)  # Увеличиваем таймаут для загрузки
            response.raise_for_status()
            return response.json()

    def get_study_analysis(self, study_id: int) -> Dict[str, Any]:
        """Получить результат анализа исследования."""
        return self._request("GET", f"/studies/{study_id}/analysis")

    def analyze_study(self, study_id: int) -> Dict[str, Any]:
        """Запустить анализ изображения исследования."""
        return self._request("POST", f"/studies/{study_id}/analyze")

    def run_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/analysis/run", json=payload)

    def confirm_analysis(self, result_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", f"/analysis/{result_id}/confirm", json=payload)

    def get_pending_analysis(self) -> Dict[str, Any]:
        return self._request("GET", "/analysis/pending")

    def get_analysis_detail(self, result_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/analysis/{result_id}")
    
    def send_result_email(self, result_id: int) -> Dict[str, Any]:
        """Отправить результаты анализа на email пациента."""
        return self._request("POST", f"/analysis/{result_id}/send-email")
    
    def list_studies(self, patient_id: int | None = None) -> list[Dict[str, Any]]:
        """Получить список всех исследований. Можно фильтровать по patient_id."""
        params = {}
        if patient_id is not None:
            params["patient_id"] = patient_id
        return self._request("GET", "/studies", params=params)
    
    def get_study(self, study_id: int) -> Dict[str, Any]:
        """Получить исследование по ID."""
        return self._request("GET", f"/studies/{study_id}")

    # ------------------------------------------------------------------ #
    # Internal mechanics
    # ------------------------------------------------------------------ #
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        print(f"[API_CLIENT] Запрос: {method.upper()} {url}")
        try:
            response = requests.request(
                method.upper(),
                url,
                params=params,
                json=json,
                timeout=self.timeout,
            )
            print(f"[API_CLIENT] Ответ: статус={response.status_code}, content-length={len(response.content)}")
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[API_CLIENT] Ошибка запроса: {exc}")
            print(f"[API_CLIENT] URL был: {url}")
            print(f"[API_CLIENT] Статус ответа: {getattr(exc.response, 'status_code', 'N/A') if hasattr(exc, 'response') else 'N/A'}")
            raise ApiError(f"{exc.__class__.__name__}: {exc}") from exc

        if not response.content:
            print(f"[API_CLIENT] Пустой ответ, возвращаем {{}}")
            return {}
        try:
            result = response.json()
            print(f"[API_CLIENT] JSON распарсен: тип={type(result)}")
            return result
        except ValueError as exc:
            print(f"[API_CLIENT] Ошибка парсинга JSON: {exc}")
            raise ApiError("Некорректный ответ сервера") from exc

