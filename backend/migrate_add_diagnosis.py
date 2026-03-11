"""Миграция: добавление колонки ai_diagnosis в таблицу analysis_results."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fluoro_backend.db"

if not DB_PATH.exists():
    print("База данных не найдена. Она будет создана при следующем запуске.")
    exit(0)

print("Добавление колонки ai_diagnosis в таблицу analysis_results...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Проверяем, существует ли колонка
    cursor.execute("PRAGMA table_info(analysis_results)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "ai_diagnosis" in columns:
        print("Колонка ai_diagnosis уже существует.")
    else:
        # Добавляем колонку
        cursor.execute(
            "ALTER TABLE analysis_results ADD COLUMN ai_diagnosis TEXT"
        )
        conn.commit()
        print("✅ Колонка ai_diagnosis успешно добавлена!")
        
except sqlite3.Error as e:
    print(f"❌ Ошибка при миграции: {e}")
    conn.rollback()
finally:
    conn.close()

print("Миграция завершена.")


