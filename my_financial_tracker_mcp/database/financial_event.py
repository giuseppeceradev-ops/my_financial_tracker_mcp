import sqlite3

from my_financial_tracker_mcp.database.database import Database

class FinancialEventsDatabase(Database):
    
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
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    description TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    google_id TEXT,
                    context TEXT
                );
            """)

    def add_event(self, description: str, amount: float, due_date: str, google_id = "", context = ""):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                INSERT INTO events (description, amount, due_date, google_id, context)
                VALUES (?, ?, ?, ?, ?)
            """, (description, amount, due_date, google_id, context))
            conn.commit()
            lastrowid = c.lastrowid

        return lastrowid

    def update_event(self, id: str, description: str, amount: float, due_date: str, google_id: str, context:str):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                UPDATE events
                SET description=?, amount=?, due_date=?, google_id=?, context=?
                WHERE ID = ?
            """, (description, amount, due_date, google_id, context, id))
            conn.commit()
            lastrowid = c.lastrowid

        return lastrowid

    def get_event(self, id: str):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                SELECT id, description, amount, due_date, google_id, context
                FROM events
                WHERE id = ?
            """, (id,))

        return c.fetchone()

    def get_events(self, id: str = None, start_date: str = None, end_date: str = None):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            query = """
                SELECT id, description, amount, due_date, google_id
                FROM events
                WHERE 1=1
            """

            params = []

            if id:
                query += " AND id = ?"
                params.append(id)

            if start_date:
                query += " AND due_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND due_date <= ?"
                params.append(end_date)

            c.execute(query, params)
            return c.fetchall()

    def remove_event(self, id):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            c.execute("""
                DELETE FROM events
               WHERE ID = ?
            """, (id,))
            conn.commit()
            lastrowid = c.lastrowid

        return lastrowid