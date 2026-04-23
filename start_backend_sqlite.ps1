# Скрипт для запуска backend с SQLite (БЕЗ PostgreSQL)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Запуск Backend с SQLite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ВАЖНО: Удаляем переменную DATABASE_URL, если она установлена
# Это заставит использовать SQLite по умолчанию
if (Test-Path Env:DATABASE_URL) {
    Write-Host "Удаление переменной DATABASE_URL..." -ForegroundColor Yellow
    Remove-Item Env:DATABASE_URL
    Write-Host "✓ Переменная удалена" -ForegroundColor Green
} else {
    Write-Host "✓ Переменная DATABASE_URL не установлена" -ForegroundColor Green
}

Write-Host ""
Write-Host "Запуск backend с SQLite..." -ForegroundColor Yellow
Write-Host ""

# Запускаем backend
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000


