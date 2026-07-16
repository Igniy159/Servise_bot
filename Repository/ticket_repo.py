from datetime import datetime
from sqlite3 import Error
from typing import Optional
from core.exceptions import RepositoryError,  IncorrectWrite
from repository.base import Repo


class TicketRepo(Repo):
    def get(self,
            filter_value: Optional[dict]=None)-> list:
        cur = self.con.cursor()
        condition = []
        sort_condition = []
        param = []
        if filter_value:
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

        where_sql = sort_sql = ""
        if condition:
            where_sql = " WHERE " + " AND ".join(condition)
        if sort_condition:
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
        except Error as e:
            raise RepositoryError(f"Error in get_tickets: {e}") from e
        tickets = [dict(row) for row in rows]
        for ticket in tickets:
            self._normalize_tickets(ticket)
        return tickets

    @staticmethod
    def _normalize_tickets(ticket:dict)-> dict:
        f = "%Y-%m-%d %H:%M:%S"
        ticket['date_create'] = datetime.strptime(ticket['date_create'], f)
        if ticket['sla_reaction_deadline']:
            ticket['sla_reaction_deadline'] = datetime.strptime(ticket['sla_reaction_deadline'], f)
        if ticket['sla_resolution_deadline']:
            ticket['sla_resolution_deadline'] = datetime.strptime(ticket['sla_resolution_deadline'],
                                                                  f)
        if ticket['date_close']:
            ticket['date_close'] = datetime.strptime(ticket['date_close'], f)
        ticket['history'] = []
        return ticket

    def get_history(self,
                    filter_value:dict)->list[dict]:
        cur = self.con.cursor()
        param = []
        condition = []
        for field, value in filter_value.items():
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
        where_sql = ""
        if condition:
            where_sql = " WHERE " + " AND ".join(condition)
        request = base_query + where_sql + sort
        try:
            res = cur.execute(request,param).fetchall()
            return [dict(r) for r in res]
        except Error as e:
            raise RepositoryError(f"Error in get_history_ticket: {e}") from e

    def create(self,
                      ticket: dict,
                      ) -> int:
        cur = self.con.cursor()

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

    def update(self,
            ticket: dict,
            ) -> None:
        cur = self.con.cursor()
        cur.execute("""UPDATE tickets SET
            current_state = (?),
            date_close = (?),
            assigned_to = (?),
            priority = (?),
            comment = (?),
            reject_comment = (?)
        WHERE ticket_id = ? """,
                    (ticket['current_state'],
                     ticket['date_close'],
                     ticket['assigned_to'],
                     ticket['priority'],
                     ticket['comment'],
                     ticket['reject_comment'],
                     ticket['ticket_id']))
        if cur.rowcount == 0:
            raise IncorrectWrite("Ticket not found")

    # HISTORY
    def insert_history(self
                      ,ticket_id: int,
                      timestamp: str,
                      user_id: int,
                      field: str | int,
                      old: str | int | None,
                      new: str | int | None,
                      ):
        cur = self.con.cursor()
        cur.execute("""INSERT INTO history"
                    (ticket_id, timestamp, user_id, field, old, new)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                    (ticket_id, timestamp, user_id, field, old, new)
                    )
