from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


class Database:
    """Thin wrapper around sqlite3 for convenience."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection


def init_db(database: Database) -> None:
    schema_statements: Iterable[str] = (
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            birth_date TEXT,
            medical_record_number TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            image_path TEXT NOT NULL,
            taken_at TEXT NOT NULL,
            priority TEXT DEFAULT 'routine',
            notes TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_id INTEGER NOT NULL REFERENCES studies(id),
            status TEXT NOT NULL,
            findings TEXT,
            confidence REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL REFERENCES analysis_results(id),
            reason TEXT NOT NULL,
            resolved INTEGER DEFAULT 0,
            resolved_at TEXT
        );
        """,
    )

    with database.connect() as conn:
        cursor = conn.cursor()
        for statement in schema_statements:
            cursor.execute(statement)
        conn.commit()


def seed_demo_data(database: Database) -> None:
    """Populate the database with demo data to visualize the UI."""
    with database.connect() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patients;")
        if cursor.fetchone()[0]:
            return

        cursor.execute(
            """
            INSERT INTO patients (full_name, birth_date, medical_record_number)
            VALUES
            ('Ирина Смирнова', '1985-02-11', 'MRN-1001'),
            ('Андрей Ковалёв', '1974-09-03', 'MRN-1002'),
            ('Мария Кузнецова', '1990-12-21', 'MRN-1003')
            ;
            """
        )

        cursor.execute(
            """
            INSERT INTO studies (patient_id, image_path, taken_at, priority, notes)
            VALUES
            (1, 'samples/fluoro_001.png', '2025-11-18T08:30:00', 'urgent', 'Повтор после лечения'),
            (2, 'samples/fluoro_002.png', '2025-11-18T09:45:00', 'routine', 'Плановый осмотр'),
            (3, 'samples/fluoro_003.png', '2025-11-17T14:10:00', 'routine', '')
            ;
            """
        )

        cursor.execute(
            """
            INSERT INTO analysis_results (study_id, status, findings, confidence)
            VALUES
            (1, 'pathology_detected', 'Подозрение на инфильтрацию верхней доли', 0.82),
            (2, 'clear', 'Патологии не обнаружены', 0.94),
            (3, 'needs_review', 'Низкая уверенность модели', 0.55)
            ;
            """
        )

        cursor.execute(
            """
            INSERT INTO alerts (analysis_id, reason, resolved)
            VALUES
            (3, 'Низкая уверенность анализа, требуется ручная проверка', 0)
            ;
            """
        )

        conn.commit()

