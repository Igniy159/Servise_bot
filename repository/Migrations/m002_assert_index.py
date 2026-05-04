def up(con):
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
