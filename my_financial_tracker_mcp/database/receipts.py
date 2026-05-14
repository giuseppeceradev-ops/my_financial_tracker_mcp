import sqlite3
import os
from rapidfuzz import process, fuzz

from my_financial_tracker_mcp.database.database import Database


class ReceiptsDatabase(Database):

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

            c.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    company TEXT,
                    total_amount REAL DEFAULT 0,
                    currency TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS receipt_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    description TEXT,
                    category_id INTEGER NOT NULL,
                    receipt_id INTEGER,
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (receipt_id) REFERENCES receipts(id)
                );
            """)

    # -------------------------
    # CATEGORY SMART RESOLUTION
    # -------------------------
    def resolve_category_id(self, category: str) -> int:
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

    # -------------------------
    # RECEIPT
    # -------------------------
    def create_receipt(self, description: str, timestamp: str, amount: float = 0, currency: str = "EUR", company: str = None) -> int:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                INSERT INTO receipts (company, description, total_amount, currency, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (company, description, amount, currency, timestamp))

            conn.commit()
            return c.lastrowid

    def recalc_receipt(self, receipt_id: int):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM receipt_items
                WHERE receipt_id = ?
            """, (receipt_id,))

            total = c.fetchone()[0]

            c.execute("""
                UPDATE receipts
                SET total_amount = ?
                WHERE id = ?
            """, (total, receipt_id))

            conn.commit()

    def get_receipt_id_from_transaction(self, tx_id: int):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT receipt_id FROM receipt_items WHERE id = ?", (tx_id,))
            row = c.fetchone()
            return row[0] if row else None

    # -------------------------
    # TRANSACTIONS
    # -------------------------
    def add_receipt_item(
        self,
        amount: float,
        description: str,
        category_id: int,
        receipt_id: int | None = None
    ):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                INSERT INTO receipt_items (amount, description, category_id, receipt_id)
                VALUES (?, ?, ?, ?)
            """, (amount, description, category_id, receipt_id))
            conn.commit()
            lastrowid = c.lastrowid

        if receipt_id != None:
            self.recalc_receipt(receipt_id)

        return lastrowid, receipt_id

    def update_transaction(
        self,
        id: int,
        amount: float,
        description: str,
        category_id: int
    ):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                UPDATE receipt_items
                SET amount = ?,
                    description = ?,
                    category_id = ?
                WHERE id = ?
            """, (amount, description, category_id, id))
            conn.commit()
            rowcount = c.rowcount

        receipt_id = self.get_receipt_id_from_transaction(id)

        if receipt_id:
            self.recalc_receipt(receipt_id)

        return rowcount

    # -------------------------
    # QUERY
    # -------------------------
    def filter_transactions(
        self, 
        id = None, 
        receipt_id = None,
        category_id=None, 
        start_date=None, 
        end_date=None):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            query = """
                SELECT t.id, t.amount, t.description, t.category_id,
                       t.receipt_id, i.company, i.currency, i.timestamp, i.total_amount
                FROM receipt_items t
                LEFT JOIN receipts i ON t.receipt_id = i.id
                WHERE 1=1
            """

            params = []

            if id:
                query += " AND t.id = ?"
                params.append(id)

            if receipt_id:
                query += " AND t.receipt_id = ?"
                params.append(receipt_id)

            if category_id:
                query += " AND t.category_id = ?"
                params.append(category_id)

            if start_date:
                query += " AND i.timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND i.timestamp <= ?"
                params.append(end_date)

            c.execute(query, params)
            return c.fetchall()

    def filter_receipts(self, 
        id:int = None,
        start_date: str = None, 
        end_date: str = None):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            query = """
                SELECT id, 
                    description, 
                    company, 
                    total_amount,
                    currency, 
                    timestamp
                FROM receipts
                WHERE 1=1
            """

            params = []

            if id != None:
                query += " AND id = ?"
                params.append(id)

            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)

            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)

            c.execute(query, params)
            return c.fetchall()

    def update_receipt(
        self,
        id,
        description: str,
        company: str,
        total_amount: float,
        timestamp: str
    ):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                UPDATE receipts
                SET description = ?, 
                company = ?,
                total_amount = ?,
                timestamp = ?
                WHERE ID = ?
            """, (description, company, total_amount, timestamp, id))
            conn.commit()
            rowcount = c.rowcount

        return rowcount

    
    def update_receipt_item(
        self,
        id,
        description: str,
        amount: str,
        category_id: float
    ):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                UPDATE receipt_items
                SET description = ?,
                amount = ?,
                category_id = ?
                WHERE ID = ?
            """, (description, amount, category_id, id))
            conn.commit()
            rowcount = c.rowcount

        return rowcount