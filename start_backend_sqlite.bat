@echo off
REM Скрипт для запуска backend с SQLite (БЕЗ PostgreSQL)

echo.
echo ========================================
echo Запуск Backend с SQLite
echo ========================================
echo.

REM ВАЖНО: Удаляем переменную DATABASE_URL, если она установлена
REM Это заставит использовать SQLite по умолчанию
if defined DATABASE_URL (
    echo Удаление переменной DATABASE_URL...
    set DATABASE_URL=
    echo ✓ Переменная удалена
) else (
    echo ✓ Переменная DATABASE_URL не установлена
)

echo.
echo Запуск backend с SQLite...
echo.

REM Запускаем backend
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000


