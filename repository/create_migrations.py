import sqlite3 as sq
from pathlib import Path
import importlib

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR /'repository'/'servise_bot.db'

MIGRATION = BASE_DIR /'repository'/'Migrations'
MIGRATIONS_PACKAGE = "repository.Migrations"

def get_connect()-> sq.Connection:
    con = sq.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sq.Row
    return con

def create_migration_shema(con):
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS migrations(
    id INTEGER PRIMARY KEY,
    name TEXT) """)

def run_migrations(con):
    migration = []
    for item in Path(MIGRATION).iterdir():
        migration.append(item.stem)
    migration.sort()

    cur = con.cursor()
    done = set([row[0] for row in cur.execute("SELECT name FROM migrations")])

    for patch in migration:
        if patch in ("__pycache__", "__init__"):
            continue
        if patch not in done:
            module = importlib.import_module(f"{MIGRATIONS_PACKAGE}.{patch}")
            module.up(con)
            cur.execute("INSERT INTO migrations (name) VALUES (?) ",(patch,))
            con.commit()
