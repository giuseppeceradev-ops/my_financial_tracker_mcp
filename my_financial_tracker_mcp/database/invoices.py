import sqlite3

from my_financial_tracker_mcp.database.database import Database

class InvoicesDatabase(Database):

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
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    company TEXT,
                    total_amount REAL NOT NULL DEFAULT 0 CHECK(total_amount >= 0),
                    currency TEXT NOT NULL,
                    emission_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    incoming BOOLEAN NOT NULL DEFAULT 1,
                    closed BOOLEAN NOT NULL DEFAULT 0
                );
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    amount REAL NOT NULL DEFAULT 0 CHECK(amount >= 0),
                    invoice_id INTEGER NOT NULL,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                );
            """)

    def recalc_invoice(self, invoice_id: int):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM invoice_items
                WHERE invoice_id = ?
            """, (invoice_id,))

            total = c.fetchone()[0]

            c.execute("""
                UPDATE invoices
                SET total_amount = ?
                WHERE id = ?
            """, (total, invoice_id))

            conn.commit()

    def create_invoice(self, company: str | None, description:str, total_amount: float, emission_date: str, due_date: str,  currency: str = "EUR", closed=False, incoming = True) -> int:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                INSERT INTO invoices (company, description, total_amount, currency, emission_date, due_date, closed, incoming)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (company, description, total_amount, currency, emission_date, due_date, closed, incoming))

            conn.commit()
            return c.lastrowid

    def add_invoice_item(
        self,
        amount: float,
        description: str,
        invoice_id: int | None = None
    ):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                INSERT INTO invoice_items (amount, description, invoice_id)
                VALUES (?, ?, ?)
            """, (amount, description, invoice_id))
            conn.commit()
            lastrowid = c.lastrowid

        if invoice_id != None:
            self.recalc_invoice(invoice_id)

        return lastrowid, invoice_id

    def update_invoice(
        self,
        id: int,
        amount: float,
        incoming: bool,
        closed: bool
    ):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                UPDATE invoices
                SET total_amount = ?, 
                incoming = ?,
                closed = ?
                WHERE ID = ?
            """, (amount, incoming, closed, id))
            conn.commit()
            rowcount = c.rowcount

        return rowcount

    def filter_invoices(self, 
        id:int = None, 
        incoming: bool = None,
        closed:bool = None, 
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
                    emission_date, 
                    due_date, 
                    incoming, 
                    closed
                FROM invoices t
                WHERE 1=1
            """

            params = []

            if id != None:
                query += " AND id = ?"
                params.append(id)

            if closed != None:
                query += " AND closed = ?"
                params.append(closed)

            if incoming != None:
                query += " AND incoming = ?"
                params.append(incoming)

            if start_date:
                query += " AND emission_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND emission_date <= ?"
                params.append(end_date)

            c.execute(query, params)
            return c.fetchall()