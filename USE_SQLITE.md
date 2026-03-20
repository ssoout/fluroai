# Использование SQLite вместо PostgreSQL

## Изменения

Теперь по умолчанию используется **SQLite** вместо PostgreSQL. Это упрощает разработку и не требует настройки отдельной базы данных.

## Как это работает

1. **По умолчанию** - используется SQLite (файл `backend/fluoro_backend.db`)
2. **Для PostgreSQL** - установите переменную окружения `DATABASE_URL`

## Запуск backend

### SQLite (по умолчанию):
```powershell
python -m uvicorn backend.app:app --reload
```

### PostgreSQL (если нужно):
```powershell
$env:DATABASE_URL = "postgresql://postgres:275235@localhost:5432/fluroai"
python -m uvicorn backend.app:app --reload
```

## Преимущества SQLite

- ✅ Не требует установки и настройки PostgreSQL
- ✅ Все данные в одном файле `backend/fluoro_backend.db`
- ✅ Проще для разработки и тестирования
- ✅ Автоматически создается при первом запуске

## Проверка

При запуске backend должно быть:
```
[DB] Используется SQLite: sqlite:///...
[DB] ✓ Таблицы успешно созданы/проверены
```

## Важно

⚠️ **Если у вас уже была PostgreSQL БД**, данные останутся там. Чтобы переключиться на SQLite:
1. Убедитесь, что переменная `DATABASE_URL` НЕ установлена
2. Перезапустите backend
3. Создайте новых пациентов и исследования

⚠️ **Файл SQLite** будет создан автоматически в папке `backend/` при первом запуске.


