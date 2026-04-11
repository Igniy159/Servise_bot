from Core.exceptions import IncorrectWrite
from Logger.logger import core_logger


#BRANCH
def branch_assert(branch_name: str, con=None):
    cur = con.cursor()
    cur.execute("INSERT INTO branch (branch_name) VALUES (?)",(branch_name,))
    core_logger.info(f"branch {branch_name} assert")

def branch_rename(branch_id: int, new_name: str,con= None):
    cur = con.cursor()
    cur.execute('UPDATE branch SET branch_name = ? WHERE branch_id = ?', (new_name, branch_id))
    if cur.rowcount == 0:
        core_logger.error(f'Branch not found')
        raise IncorrectWrite("Branch not found")
    core_logger.info(f"branch {branch_id} rename {new_name}")

def branch_soft_del(branch_id: int, con=None):
    cur = con.cursor()
    cur.execute('UPDATE branch SET branch_activity = 0 WHERE branch_id = ?', (branch_id,))
    if cur.rowcount == 0:
        core_logger.error("Branch not found")
        raise IncorrectWrite("Branch not found")
    core_logger.info(f'branch {branch_id} not activity')

def branch_activate(branch_id:int,con=None):
    cur = con.cursor()
    cur.execute('UPDATE branch SET branch_activity = 1 WHERE branch_id = ?', (branch_id,))
    if cur.rowcount == 0:
        core_logger.error("Branch not found")
        raise IncorrectWrite("Branch not found")
    core_logger.info(f'branch {branch_id} reactivity')


#USERS
def user_assert(user_name: str, api_user_id: int,role_id: int,
                depart_id=None, branch_id=None, con=None):
    cur = con.cursor()
    cur.execute(
        "INSERT INTO users (user_name, api_user_id, role_id, depart_id, branch_id) VALUES (?, ?, ?, ?, ?)",
        (user_name, api_user_id, role_id, depart_id, branch_id))
    core_logger.info(f"user {user_name} assert in bd")


def user_soft_del(user_id: int, con=None):
    cur = con.cursor()
    cur.execute('UPDATE users SET user_activity = 0 WHERE user_id = ?', (user_id,))
    if cur.rowcount == 0:
        core_logger.error("User not found")
        raise IncorrectWrite("User not found")
    core_logger.info(f"user {user_id} deactivate")

def user_activate(user_id: int, con= None):
    cur = con.cursor()
    cur.execute('UPDATE users SET user_activity = 1 WHERE user_id = ?', (user_id,))
    if cur.rowcount == 0:
        core_logger.error(f"User {user_id} not found")
        raise IncorrectWrite("User not found")
    core_logger.info(f"user {user_id} activate")

def update_user_params(user_id:int, role_id:int,branch_id:int,depart_id:int,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE users SET role_id = ?, branch_id = ?, depart_id = ?
                WHERE user_id = ?""", (role_id,branch_id,depart_id, user_id))
    if cur.rowcount == 0:
        core_logger.error(f"User {user_id} not found")
        raise IncorrectWrite("User not found")
    core_logger.info(f"user {user_id} change role = {role_id}, branch ={branch_id}, depart= {depart_id}")

def update_user_name(user_id:int, user_name:str,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE users SET user_name = ? WHERE user_id = ?""", (user_name, user_id))
    if cur.rowcount == 0:
        core_logger.error(f"User {user_id} not found")
        raise IncorrectWrite("User not found")
    core_logger.info(f"user {user_id} change name = {user_name}")


#HISTORY
def insert_history_record(ticket_id, timestamp, user_id, field, old, new, con=None):
    cur = con.cursor()
    cur.execute("INSERT INTO history (ticket_id, timestamp, user_id, field, old, new) VALUES (?, ?, ?, ?, ?, ?)",
                (ticket_id, timestamp, user_id, field, old, new)
                )

#TICKETS
def ticket_assert(ticket:dict,con=None)-> int:
    cur = con.cursor()
    cur.execute("""INSERT INTO tickets (
                             creator_id, branch_id, event_type, problem_category, problem_name,
                             problem_class, problem_type, zone, scenario, target,
                             date_create, sla_reaction_deadline, sla_resolution_deadline, current_state,
                             date_close, assigned_to, reject_comment, comment,priority) 
                             VALUES (?, ?, ?, ?, ?,
                                 ?, ?, ?, ?, ?, 
                                 ?, ?, ?, ?, ?,
                                 ?, ?, ?, ?)""",
                (ticket['creator_id'],
                 ticket['branch_id'],
                 ticket['event_type'],
                 ticket['problem_category'],
                 ticket['problem_name'],
                 ticket['problem_class'],
                 ticket['problem_type'],
                 ticket['zone'],
                 ticket['scenario'],
                 ticket['target'],
                 ticket['date_create'],
                 ticket['sla_reaction_deadline'],
                 ticket['sla_resolution_deadline'],
                 ticket['current_state'],
                 ticket['date_close'],
                 ticket['assigned_to'],
                 ticket['reject_comment'],
                 ticket['comment'],
                 ticket['priority']
                 ))

    return cur.lastrowid

def ticket_state(ticket_id, new_state,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE tickets SET current_state = (?) WHERE ticket_id = (?)""", (new_state, ticket_id))
def assign_ticket(ticket_id, user_id,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE tickets SET assigned_to = ? WHERE ticket_id = ? """, (user_id, ticket_id))
def close_ticket(ticket_id, data_close,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE tickets SET date_close = (?) WHERE ticket_id = (?)""", (data_close, ticket_id))
def reject_ticket(ticket_id, reject_comm,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE tickets SET reject_comment = (?) WHERE ticket_id = (?)""", (reject_comm, ticket_id))
def change_priority(ticket_id, priority_id,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE tickets SET priority = (?) WHERE ticket_id = (?)""", (priority_id, ticket_id))
def update_comment(ticket_id, new_comment,con=None):
    cur = con.cursor()
    cur.execute("""UPDATE tickets SET comment = (?) WHERE ticket_id = (?)""", (new_comment, ticket_id))





