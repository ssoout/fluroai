@echo off
REM Скрипт для перезапуска backend с правильной настройкой БД

echo.
echo ========================================
echo Перезапуск Backend
echo ========================================
echo.

REM Устанавливаем переменную окружения для PostgreSQL
set DATABASE_URL=postgresql://postgres:275235@localhost:5432/fluroai

echo DATABASE_URL установлен: %DATABASE_URL%
echo.
echo Запуск backend с автоматической перезагрузкой...
echo.

REM Запускаем backend с --reload для автоматической перезагрузки при изменениях
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000


