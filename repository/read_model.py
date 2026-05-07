import sqlite3 as sq
from datetime import datetime
from typing import Optional
from core.exceptions import RepositoryError


#BRANCH
def get_branch_with_data(con: sq.Connection,
                         filter_value: Optional[dict] = None)-> list[dict]:
    cur = con.cursor()
    base_query = """SELECT b.branch_id,
                            b.branch_name,
                            u.user_name AS branch_manager
                            FROM branch AS b
                            LEFT JOIN users AS u ON b.branch_id = u.branch_id AND role_id = 2"""
    conditions = []
    params = []
    if filter_value:
        for key, val in filter_value.items():
            if key == "branch_id":
                conditions.append("b.branch_id = ?")
                params.append(val)
            elif key == "branch_name":
                conditions.append("b.branch_name = ?")
                params.append(val)
            elif key == "branch_activity":
                conditions.append("b.branch_activity = ?")
                params.append(val)
    where_sql = ''
    if conditions:
        where_sql = " WHERE " + " AND ".join(conditions)
    request = base_query + where_sql
    try:
        rows = cur.execute(request, params).fetchall()
        return [dict(row) for row in rows]
    except sq.Error as e :
        raise RepositoryError(f"Error in get_branch_with_data: {e}") from e

#USERS
def get_users_with_data(con: sq.Connection,
                        filter_value: Optional[dict]=None)-> list[dict]:
    cur = con.cursor()
    condition = []
    param = []
    if filter_value:
        for key, val in filter_value.items():
            if key == "user_id":
                condition.append("u.user_id = ?")
                param.append(val)
            elif key == "api_user_id":
                condition.append("u.api_user_id = (?)")
                param.append(val)
            elif key == "user_branch_id":
                condition.append("u.branch_id = ?")
                param.append(val)
            elif key == "user_depart_id":
                condition.append("u.depart_id = ?")
                param.append(val)
            elif key == "role_id":
                condition.append("u.role_id = ?")
                param.append(val)
            elif key == "user_activity":
                condition.append("u.user_activity = ?")
                param.append(val)
    where_sql = ''
    if condition:
        where_sql = " WHERE " + " AND ".join(condition)

    base_query = """SELECT u.user_id,
                           u.user_name,
                           u.api_user_id,
                           r.role_name,
                           u.depart_id,
                           d.depart_name,
                           u.branch_id,
                           b.branch_name
                           FROM users AS u
                           JOIN role AS r ON u.role_id = r.role_id
                           LEFT JOIN department AS d ON d.depart_id = u.depart_id
                           LEFT JOIN branch AS b ON b.branch_id = u.branch_id"""
    request = base_query + where_sql

    try:
        rows = cur.execute(request, param).fetchall()
        return [dict(row) for row in rows]
    except sq.Error as e:
        raise RepositoryError(f"Error in get_tickets: {e}") from e

#TICKET
def get_tickets_with_data(con:sq.Connection,
                          filter_value: Optional[dict]=None)-> list:
    cur = con.cursor()
    condition = []
    sort_condition = []
    param = []
    for key, val in filter_value.items():
        if key == "ticket_id":
            condition.append("t.ticket_id = ?")
            param.append(val)
        elif key == "zone":
            condition.append("t.zone = ?")
            param.append(val)
        elif key == "branch_id":
            condition.append("t.branch_id = ?")
            param.append(val)
        elif key == "depart_id":
            condition.append(" t.target = ? ")
            param.append(val)
        elif key == "creator_id":
            condition.append("t.creator_id = ? ")
            param.append(val)
        elif key == "status":
            condition.append("t.current_state = ?")
            param.append(val)
        elif key == "priority":
            condition.append("t.priority = ?")
            param.append(val)

        elif key == 'sort_priority':
            if val.lower() in ("asc", "desc"):
                sort_condition.append(f"p.priority_id {val.upper()}")
        elif key == "sort_status":
            if val.lower() in ("asc", "desc"):
                sort_condition.append(f"st.status_id {val.upper()}")


    where_sql = " WHERE " + " AND ".join(condition)
    sort_sql = " ORDER BY " + ", ".join(sort_condition)

    base_query = """SELECT t.ticket_id,
                                   t.creator_id,
                                   cr.user_name AS creator_name,
                                   t.branch_id,
                                   b.branch_name,
                                   t.event_type,
                                   t.problem_category,
                                   t.problem_name,
                                   t.problem_class,
                                   t.problem_type,
                                   t.zone,
                                   t.scenario,
                                   d.depart_name AS target,
                                   t.date_create,
                                   t.sla_reaction_deadline,
                                   t.sla_resolution_deadline,
                                   st.status_name AS current_state,
                                   t.date_close,
                                   asig.user_name AS assigned_to,
                                   t.reject_comment,
                                   t.comment,
                                   p.priority_name AS priority
                                   FROM tickets AS t 
                                   JOIN users AS cr ON t.creator_id = cr.user_id
                                   LEFT JOIN users AS asig ON t.assigned_to = asig.user_id
                                   JOIN branch AS b ON t.branch_id = b.branch_id
                                    JOIN department AS d ON t.target = d.depart_id
                                   JOIN priority AS p ON t.priority = p.priority_id
                                   JOIN ticket_status AS st ON t.current_state = st.status_id
                                   """
    request = base_query + where_sql + sort_sql
    try:
        rows = cur.execute(request, param).fetchall()
    except sq.Error as e:
        raise RepositoryError(f"Error in get_tickets: {e}") from e
    results = [dict(row) for row in rows]
    for res in results:
        res['date_create'] = datetime.strptime(res['date_create'], "%Y-%m-%d %H:%M:%S")
        res['sla_reaction_deadline'] = datetime.strptime(res['sla_reaction_deadline'], "%Y-%m-%d %H:%M:%S") if res[
            'sla_reaction_deadline'] else None
        res['sla_resolution_deadline'] = datetime.strptime(res['sla_resolution_deadline'], "%Y-%m-%d %H:%M:%S") if res[

            'sla_resolution_deadline'] else None
        res['date_close'] = datetime.strptime(res['date_close'], "%Y-%m-%d %H:%M:%S") if res['date_close'] else None
        res['history'] = []
    return results

#HISTORY
def fetch_history_ticket(con:sq.Connection,
                         filter_value:dict)->list[dict]:
    cur = con.cursor()
    param = []
    condition = []

    for field, value in filter_value:
        if field == 'ticket_id':
            param.append(value)
            condition.append("h.ticket_id = ?")
        elif field == 'branch_id':
            param.append(value)
            condition.append("t.branch_id = ?")
        elif field == "depart_id":
            param.append(value)
            condition.append("t.target = ?")
        elif field == "creator_id":
            param.append(value)
            condition.append("t.creator_id = ?")

    base_query = """
    SELECT 
            h.patch_id, 
            h.ticket_id, 
            h.timestamp,
            h.field,
            h.old,
        CASE
            WHEN h.field = 'assigned_to' THEN asiq.user_name
            ELSE h.new
        END AS new_value,
            u.user_name, 
            r.role_name
        FROM history AS h 
        LEFT JOIN users AS asiq 
            ON h.new = CAST(asiq.user_id AS TEXT) AND h.field = 'assigned_to'
        JOIN users AS u 
            ON h.user_id = u.user_id
        JOIN role AS r 
            ON u.role_id = r.role_id
        JOIN tickets AS t
            ON t.id = h.ticket_id
            """
    sort = "ORDER BY h.timestamp"
    where_sql = " WHERE " + " AND ".join(condition)
    request = base_query + where_sql + sort
    try:
        res = cur.execute(request,param).fetchall()
        return [dict(r) for r in res]
    except sq.Error as e :
        raise RepositoryError(f"Error in get_history_ticket: {e}") from e
