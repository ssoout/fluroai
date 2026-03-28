# Скрипт для перезапуска backend с правильной настройкой БД

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Перезапуск Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Устанавливаем переменную окружения для PostgreSQL
$env:DATABASE_URL = "postgresql://postgres:275235@localhost:5432/fluroai"

Write-Host "DATABASE_URL установлен: $env:DATABASE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Запуск backend с автоматической перезагрузкой..." -ForegroundColor Yellow
Write-Host ""

# Запускаем backend с --reload для автоматической перезагрузки при изменениях
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000


