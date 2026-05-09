"""SQLite connection and schema initialization with version tracking."""
import os
import sqlite3
from pathlib import Path

_data_dir = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent)))
DB_PATH = _data_dir / "life.db"

# Increment when adding new migrations below.
SCHEMA_VERSION = 1


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _get_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


# Each entry: (version_number, sql_to_apply)
_MIGRATIONS: list[tuple[int, str]] = [
    (1, """
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT    NOT NULL DEFAULT '',
            status      TEXT    NOT NULL DEFAULT 'todo'
                        CHECK(status IN ('todo','in_progress','done','cancelled')),
            priority    TEXT    NOT NULL DEFAULT 'normal'
                        CHECK(priority IN ('low','normal','high')),
            due_date    TEXT,
            tags        TEXT    NOT NULL DEFAULT '[]',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            start_time  TEXT    NOT NULL,
            end_time    TEXT,
            location    TEXT    NOT NULL DEFAULT '',
            description TEXT    NOT NULL DEFAULT '',
            recurrence  TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            content     TEXT    NOT NULL DEFAULT '',
            tags        TEXT    NOT NULL DEFAULT '[]',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
            USING fts5(title, content, content='notes', content_rowid='id');

        CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
            INSERT INTO notes_fts(rowid, title, content)
            VALUES (new.id, new.title, new.content);
        END;

        CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, title, content)
            VALUES ('delete', old.id, old.title, old.content);
        END;

        CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, title, content)
            VALUES ('delete', old.id, old.title, old.content);
            INSERT INTO notes_fts(rowid, title, content)
            VALUES (new.id, new.title, new.content);
        END;

        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            amount      REAL    NOT NULL CHECK(amount > 0),
            type        TEXT    NOT NULL DEFAULT 'expense'
                        CHECK(type IN ('expense','income')),
            category    TEXT    NOT NULL DEFAULT '',
            note        TEXT    NOT NULL DEFAULT '',
            date        TEXT    NOT NULL DEFAULT (date('now')),
            tags        TEXT    NOT NULL DEFAULT '[]',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_transactions_date     ON transactions(date);
        CREATE INDEX IF NOT EXISTS idx_transactions_type     ON transactions(type);
        CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);

        CREATE TABLE IF NOT EXISTS health_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            type        TEXT    NOT NULL,
            subject     TEXT    NOT NULL DEFAULT 'self',
            start_time  TEXT    NOT NULL,
            end_time    TEXT,
            value       REAL,
            unit        TEXT    NOT NULL DEFAULT '',
            notes       TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_health_logs_type       ON health_logs(type);
        CREATE INDEX IF NOT EXISTS idx_health_logs_subject    ON health_logs(subject);
        CREATE INDEX IF NOT EXISTS idx_health_logs_start_time ON health_logs(start_time);

        CREATE TABLE IF NOT EXISTS habits (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            target_value REAL,
            unit         TEXT    NOT NULL DEFAULT '',
            frequency    TEXT    NOT NULL DEFAULT 'daily'
                         CHECK(frequency IN ('daily','weekly')),
            active       INTEGER NOT NULL DEFAULT 1,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS habit_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id   INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            date       TEXT    NOT NULL,
            value      REAL,
            notes      TEXT    NOT NULL DEFAULT '',
            created_at TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(habit_id, date)
        );

        CREATE INDEX IF NOT EXISTS idx_habit_logs_habit_id ON habit_logs(habit_id);
        CREATE INDEX IF NOT EXISTS idx_habit_logs_date     ON habit_logs(date);
    """),
]


def init_db() -> None:
    """Apply all pending migrations in order."""
    with get_conn() as conn:
        current = _get_version(conn)
        for version, sql in _MIGRATIONS:
            if version > current:
                conn.executescript(sql)
                _set_version(conn, version)


def db_status() -> dict:
    """Return schema version and row counts for each table."""
    with get_conn() as conn:
        version = _get_version(conn)
        counts = {}
        for table in ("tasks", "events", "notes", "transactions", "health_logs", "habits", "habit_logs"):
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0]
        return {"schema_version": version, "latest_version": SCHEMA_VERSION, "rows": counts}


def reset_db() -> None:
    """Drop all tables and re-run migrations. Destructive — use with care."""
    with get_conn() as conn:
        conn.executescript("""
            DROP TABLE IF EXISTS notes_fts;
            DROP TRIGGER IF EXISTS notes_ai;
            DROP TRIGGER IF EXISTS notes_ad;
            DROP TRIGGER IF EXISTS notes_au;
            DROP TABLE IF EXISTS notes;
            DROP TABLE IF EXISTS events;
            DROP TABLE IF EXISTS tasks;
            DROP TABLE IF EXISTS transactions;
            DROP TABLE IF EXISTS health_logs;
        """)
        _set_version(conn, 0)
    init_db()


