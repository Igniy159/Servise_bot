from core.loader import raw_config

def up(con):
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
        for key in raw_config['enum']['TICKET_STATUS']:
            if key not in ('CLOSED', 'CANCELLED'):
                state = "open"
            else:
                state = "close"
            cur.execute("INSERT INTO ticket_status (status_name, state) VALUES (?, ?)",
                        (key, state))
    cur.execute(""" CREATE TABLE IF NOT EXISTS department(
    depart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    depart_name TEXT
    )""")
    if not cur.execute("SELECT depart_id FROM department").fetchall():
        for dep in raw_config['enum']['DEPARTMENTS'].keys():
            cur.execute("INSERT INTO department (depart_name) VALUES (?)", (dep,))

    cur.execute("""CREATE TABLE IF NOT EXISTS priority(
    priority_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    priority_name TEXT)
    """)
    if not cur.execute("SELECT priority_id FROM priority").fetchall():
        for priority in raw_config['enum']['priority']:
            cur.execute("INSERT INTO priority (priority_name) VALUES (?)", (priority,))

    cur.execute(""" CREATE TABLE IF NOT EXISTS role(
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT
    )""")
    if not cur.execute("SELECT role_id FROM role").fetchall():
        for role in raw_config['enum']['ROLES']:
            cur.execute("INSERT INTO role (role_name) VALUES (?)", (role,))

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
    target INTEGER,
    problem_name TEXT,
    problem_category TEXT,
    problem_type TEXT, 
    zone TEXT,
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
