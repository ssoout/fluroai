# Настройка базы данных

## PostgreSQL

1. Создайте базу данных:
```sql
CREATE DATABASE fluroai;
```

2. Установите драйвер PostgreSQL:
```bash
pip install psycopg2-binary
```

3. Настройте переменную окружения:
```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://username:password@localhost:5432/fluroai"

# Windows CMD
set DATABASE_URL=postgresql://username:password@localhost:5432/fluroai

# Linux/Mac
export DATABASE_URL="postgresql://username:password@localhost:5432/fluroai"
```

Или создайте файл `.env` в папке `backend/`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/fluroai
```

4. Запустите backend - таблицы создадутся автоматически:
```bash
python -m uvicorn backend.app:app --reload
```

## SQLite (по умолчанию)

Если не указать `DATABASE_URL`, будет использоваться SQLite (файл `backend/fluoro_backend.db`).

## Формат строки подключения PostgreSQL

```
postgresql://[user[:password]@][host][:port][/dbname]
```

Примеры:
- `postgresql://postgres:mypassword@localhost:5432/fluroai`
- `postgresql://user:pass@127.0.0.1:5432/fluroai`


