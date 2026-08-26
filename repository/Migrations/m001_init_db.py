from core.enums import State, Role, Depart


def up(con):
    cur = con.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS branch(
    branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_name TEXT UNIQUE,
    branch_activity INTEGER DEFAULT 1
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS ticket_status(
    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    status_name TEXT,
    state TEXT)
    """)
    if not cur.execute("SELECT status_id FROM ticket_status").fetchall():
        for key in State:
            if key.name not in ('CLOSED', 'CANCELLED'):
                state = "open"
            else:
                state = "close"
            cur.execute("INSERT INTO ticket_status (status_name, state) VALUES (?, ?)",
                        (key.name, state))
    cur.execute(""" CREATE TABLE IF NOT EXISTS department(
    depart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    depart_name TEXT
    )""")
    if not cur.execute("SELECT depart_id FROM department").fetchall():
        for dep in Depart:
            cur.execute("INSERT INTO department (depart_name) VALUES (?)", (dep.name,))


    cur.execute(""" CREATE TABLE IF NOT EXISTS role(
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT
    )""")
    if not cur.execute("SELECT role_id FROM role").fetchall():
        for role in Role:
            cur.execute("INSERT INTO role (role_name) VALUES (?)", (role.name,))

    cur.execute(""" CREATE TABLE IF NOT EXISTS users(
     user_id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_name TEXT,
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

    cur.execute("""CREATE TABLE IF NOT EXISTS rules(
    code INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT,
    class TEXT,
    name TEXT UNIQUE,
    target_id INTEGER,
    FOREIGN KEY(target_id) REFERENCES department (depart_id)
    )""")
    cur.execute(""" CREATE TABLE IF NOT EXISTS tickets(
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_ticket INTEGER,
    severity TEXT,
    actor_id INTEGER,
    branch_id INTEGER,
    comment TEXT,
    state_id INTEGER,
    assigned_to INTEGER,
    file_id TEXT,
    date_create TEXT,
    FOREIGN KEY(code_ticket) REFERENCES rules (code),
    FOREIGN KEY(branch_id) REFERENCES branch (branch_id),
    FOREIGN KEY(actor_id) REFERENCES users (user_id),
    FOREIGN KEY(assigned_to) REFERENCES users (user_id)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts(
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_alert INTEGER,
    creator_id INTEGER,
    branch_id INTEGER,
    date_create TEXT,
    comment TEXT,
    FOREIGN KEY(creator_id) REFERENCES users(user_id),
    FOREIGN KEY(code_alert) REFERENCES rules (code),
    FOREIGN KEY(branch_id) REFERENCES branch (branch_id)
    )""")
    cur.execute(""" CREATE TABLE IF NOT EXISTS history(
    patch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,
    timestamp TEXT,
    user_id INTEGER,
    field TEXT,
    old TEXT,
    new TEXT,
    FOREIGN KEY(user_id) REFERENCES users (user_id),
    FOREIGN KEY(ticket_id) REFERENCES tickets (ticket_id)
    )""")
