import sqlite3 as sq
from Core.loader import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR /'Repository'/'servise_bot.db'

def get_connect():
    con = sq.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sq.Row
    return con

def init_db():
    with get_connect() as con:
        cur = con.cursor()
        cur.execute(""" CREATE TABLE IF NOT EXISTS branch(
        branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_name TEXT UNIQUE,
        branch_activity INTEGER DEFAULT 1
        )""")

        cur.execute(""" CREATE TABLE IF NOT EXISTS history(
        patch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        timestamp TEXT,
        user_id INTEGER,
        field TEXT,
        old TEXT,
        new TEXT,
        FOREIGN KEY(user_id) REFERENCES users (user_id)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS ticket_status(
        status_id INTEGER PRIMARY KEY AUTOINCREMENT,
        status_name TEXT,
        state TEXT)
        """)
        if not cur.execute("SELECT status_id FROM ticket_status").fetchall():
            dep = [i for i in config['enum']['TICKET_STATUS'].keys()]
            for i in range(len(dep)):
                if dep[i] not in ('CLOSED', 'CANCELLED'):
                    state = "open"
                else:
                    state = "close"
                cur.execute("INSERT INTO ticket_status (status_name, state) VALUES (?, ?)", (dep[i], state))

        cur.execute(""" CREATE TABLE IF NOT EXISTS department(
        depart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        depart_name TEXT
        )""")
        if not cur.execute("SELECT depart_id FROM department").fetchall():
            dep = [i for i in config['enum']['DEPARTMENTS'].keys()]
            for i in range(len(dep)):
                cur.execute("INSERT INTO department (depart_name) VALUES (?)", (dep[i],))

        cur.execute("""CREATE TABLE IF NOT EXISTS priority(
        priority_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        priority_name TEXT)
        """)
        if not cur.execute("SELECT priority_id FROM priority").fetchall():
            dep = [i for i in config['enum']['priority'].keys()]
            for i in range(len(dep)):
                cur.execute("INSERT INTO priority (priority_name) VALUES (?)", (dep[i],))

        cur.execute(""" CREATE TABLE IF NOT EXISTS role(
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT
        )""")
        if not cur.execute("SELECT role_id FROM role").fetchall():
            dep = [i for i in config['enum']['ROLES'].keys()]
            for i in range(len(dep)):
                cur.execute("INSERT INTO role (role_name) VALUES (?)", (dep[i],))

        cur.execute(""" CREATE TABLE IF NOT EXISTS users(
         user_id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_name TEXT UNIQUE,
         api_user_id INTEGER UNIQUE,
         role_id INTEGER NOT NULL,
         depart_id INTEGER,
         branch_id INTEGER,
         user_activity INTEGER DEFAULT 1,
         FOREIGN KEY(depart_id) REFERENCES department (depart_id),
         FOREIGN KEY(branch_id) REFERENCES branch (branch_id),
         FOREIGN KEY(role_id) REFERENCES role(role_id),
         CHECK (
         branch_id IS NOT NULL AND depart_id IS NULL
         OR
         branch_id IS NULL AND depart_id IS NOT NULL
         OR 
         branch_id IS NULL AND depart_id IS NULL)
         )""")

        cur.execute(""" CREATE TABLE IF NOT EXISTS tickets(
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_id INTEGER,
        branch_id INTEGER,
        event_type TEXT,
        problem_category TEXT,
        problem_name TEXT,
        problem_class TEXT,
        problem_type TEXT,
        zone TEXT,
        scenario TEXT,
        target INTEGER,
        date_create TEXT,
        sla_reaction_deadline TEXT,
        sla_resolution_deadline TEXT,
        current_state INTEGER,
        date_close TEXT,
        assigned_to INTEGER,
        reject_comment TEXT,
        comment TEXT,
        priority INTEGER,
        FOREIGN KEY(priority) REFERENCES priority(priority_id),
        FOREIGN KEY(creator_id) REFERENCES users (user_id),
        FOREIGN KEY(branch_id) REFERENCES branch (branch_id),
        FOREIGN KEY(target) REFERENCES department (depart_id),
        FOREIGN KEY(assigned_to) REFERENCES users (user_id)
        )""")

def assert_index():
    with get_connect() as con:
        cur = con.cursor()
        cur.executescript("""
        CREATE INDEX IF NOT EXISTS idx_tickets_creator_id ON tickets(creator_id);
        CREATE INDEX IF NOT EXISTS idx_tickets_branch_id ON tickets(branch_id);
        CREATE INDEX IF NOT EXISTS idx_tickets_depart_id ON tickets(target);
        CREATE INDEX IF NOT EXISTS idx_tickets_state ON tickets(current_state);
        CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
        CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to);

        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_api_user_id ON users(api_user_id);
        CREATE INDEX IF NOT EXISTS idx_users_branch_id ON users(branch_id);
        CREATE INDEX IF NOT EXISTS idx_users_depart_id ON users(depart_id);
        CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);

        CREATE INDEX IF NOT EXISTS idx_history_ticket_id ON history(ticket_id);
        """)