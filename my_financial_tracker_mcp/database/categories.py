import sqlite3
import os
from rapidfuzz import process, fuzz

from my_financial_tracker_mcp.database.database import Database


class CategoriesDatabase(Database):

    def __init__(self, folder_path:str, db_name: str):
        super().__init__(folder_path, db_name)

    # -------------------------
    # INIT
    # -------------------------
    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            c = conn.cursor()

            c.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL UNIQUE
                );
            """)
    # -------------------------
    # CATEGORY SMART RESOLUTION
    # -------------------------
    async def resolve_category_id(self, category: str) -> int:
        category = category.strip().lower()

        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("SELECT id, description FROM categories")
            rows = c.fetchall()

            if not rows:
                return self._create_category(conn, category)

            for r in rows:
                if r[1].lower() == category:
                    return r[0]

            match = process.extractOne(
                category,
                [r[1] for r in rows],
                scorer=fuzz.WRatio
            )

            if match and match[1] >= 85:
                for r in rows:
                    if r[1] == match[0]:
                        return r[0]

            return self._create_category(conn, category)

    def _create_category(self, conn, description: str) -> int:
        c = conn.cursor()
        c.execute("INSERT INTO categories (description) VALUES (?)", (description,))
        conn.commit()
        return c.lastrowid

    def get_category(self, id: str):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                SELECT id, description
                FROM categories
                WHERE id = ?
            """, (id,))

        return c.fetchone()