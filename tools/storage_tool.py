"""
StorageTool — SQLite-backed persistence for transactions, budgets, and memory.
"""

import sqlite3
import json
from datetime import datetime
from config import DB_PATH, DEFAULT_BUDGET
from models.transaction import Transaction


class StorageTool:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    amount      REAL,
                    category    TEXT,
                    merchant    TEXT,
                    deadline    TEXT,
                    payment_link TEXT,
                    importance  TEXT,
                    source      TEXT DEFAULT 'email',
                    status      TEXT DEFAULT 'pending',
                    email_id    TEXT,
                    created_at  TEXT
                );

                CREATE TABLE IF NOT EXISTS budgets (
                    category TEXT PRIMARY KEY,
                    monthly_limit REAL,
                    updated_at    TEXT
                );

                CREATE TABLE IF NOT EXISTS memory (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            # Seed default budgets if empty
            cur = conn.execute("SELECT COUNT(*) FROM budgets")
            if cur.fetchone()[0] == 0:
                for cat, lim in DEFAULT_BUDGET.items():
                    conn.execute(
                        "INSERT OR IGNORE INTO budgets VALUES (?,?,?)",
                        (cat, lim, datetime.now().isoformat())
                    )

    def _conn(self):
        return sqlite3.connect(self.db_path)

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------
    def save_transaction(self, txn: Transaction) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO transactions
                   (description,amount,category,merchant,deadline,
                    payment_link,importance,source,status,email_id,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (txn.description, txn.amount, txn.category, txn.merchant,
                 txn.deadline, txn.payment_link, txn.importance,
                 txn.source, txn.status, txn.email_id, txn.created_at)
            )
            return cur.lastrowid

    def update_status(self, txn_id: int, status: str):
        with self._conn() as conn:
            conn.execute("UPDATE transactions SET status=? WHERE id=?", (status, txn_id))

    def get_transactions(self, month: str = None, category: str = None):
        """Return transactions optionally filtered by YYYY-MM month and/or category."""
        query  = "SELECT * FROM transactions WHERE 1=1"
        params = []
        if month:
            query += " AND strftime('%Y-%m', created_at) = ?"
            params.append(month)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY created_at DESC"
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_all_transactions(self, limit: int = 200):
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM transactions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Budgets
    # ------------------------------------------------------------------
    def get_budgets(self) -> dict:
        with self._conn() as conn:
            rows = conn.execute("SELECT category, monthly_limit FROM budgets").fetchall()
        return {r[0]: r[1] for r in rows}

    def update_budget(self, category: str, limit: float):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO budgets VALUES (?,?,?)",
                (category, limit, datetime.now().isoformat())
            )

    def get_monthly_spent(self, category: str, month: str = None) -> float:
        if not month:
            month = datetime.now().strftime("%Y-%m")
        with self._conn() as conn:
            row = conn.execute(
                """SELECT COALESCE(SUM(amount),0) FROM transactions
                   WHERE category=? AND strftime('%Y-%m', created_at)=?
                   AND status IN ('paid','reminded')""",
                (category, month)
            ).fetchone()
        return row[0] if row else 0.0

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------
    def save_memory(self, key: str, value):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memory VALUES (?,?)",
                (key, json.dumps(value))
            )

    def load_memory(self, key: str, default=None):
        with self._conn() as conn:
            row = conn.execute("SELECT value FROM memory WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default
