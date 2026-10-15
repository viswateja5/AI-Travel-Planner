from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from config import DB_PATH
from utils.helpers import ensure_directory
from utils.logger import AppLogger

logger = AppLogger("database").get_logger()


class TripHistoryStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or DB_PATH)
        ensure_directory(self.db_path.parent)
        self._initialize_db()

    def _initialize_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    destination TEXT NOT NULL,
                    budget REAL NOT NULL,
                    travelers INTEGER NOT NULL,
                    generated_at TEXT NOT NULL,
                    output_path TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_trip(self, destination: str, budget: float, travelers: int, output_path: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO trips (destination, budget, travelers, generated_at, output_path) VALUES (?, ?, ?, ?, ?)",
                (destination, budget, travelers, __import__("datetime").datetime.utcnow().isoformat(), output_path),
            )
            conn.commit()
            logger.info("Saved trip history for %s", destination)
