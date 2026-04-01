# Скрипт для настройки PostgreSQL подключения в PowerShell
# Замените значения на свои!

$env:DATABASE_URL = "postgresql://postgres:275235@localhost:5432/fluroai"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Настройка подключения к PostgreSQL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "DATABASE_URL установлен: $env:DATABASE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Теперь запустите backend:" -ForegroundColor Yellow
Write-Host "python -m uvicorn backend.app:app --reload" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Запускаем backend с установленной переменной
python -m uvicorn backend.app:app --reload

