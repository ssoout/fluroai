@echo off
REM Скрипт для настройки PostgreSQL подключения
REM Замените значения на свои!

set DATABASE_URL=postgresql://postgres:275235@localhost:5432/fluroai

echo.
echo ========================================
echo Настройка подключения к PostgreSQL
echo ========================================
echo.
echo DATABASE_URL установлен: %DATABASE_URL%
echo.
echo Теперь запустите backend:
echo python -m uvicorn backend.app:app --reload
echo.
echo ========================================
echo.

REM Запускаем backend с установленной переменной
python -m uvicorn backend.app:app --reload

