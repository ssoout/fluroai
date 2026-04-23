# Скрипт для чистого запуска backend с SQLite

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Чистый запуск Backend с SQLite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Удаляем переменную DATABASE_URL
if (Test-Path Env:DATABASE_URL) {
    Remove-Item Env:DATABASE_URL
    Write-Host "✓ Переменная DATABASE_URL удалена" -ForegroundColor Green
} else {
    Write-Host "✓ Переменная DATABASE_URL не установлена" -ForegroundColor Green
}

# Проверяем
Write-Host ""
Write-Host "Проверка переменной:" -ForegroundColor Yellow
if ($env:DATABASE_URL) {
    Write-Host "  ⚠ DATABASE_URL все еще установлена: $env:DATABASE_URL" -ForegroundColor Red
    Write-Host "  Попробуйте закрыть терминал и открыть новый" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ DATABASE_URL не установлена - будет использоваться SQLite" -ForegroundColor Green
}

Write-Host ""
Write-Host "Запуск backend..." -ForegroundColor Yellow
Write-Host ""

# Запускаем backend
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000


