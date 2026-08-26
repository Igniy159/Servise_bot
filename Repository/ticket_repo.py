from sqlite3 import Error
from typing import Optional
from core.exceptions import RepositoryError, IncorrectWrite
from core.ticket_core import Ticket,TicketView
from repository.base import Repo
from repository.mapper_repo import MapperState


class TicketRepo(Repo):
    def get(self,
            filter_value: Optional[dict]=None)-> list[TicketView]:
        cur = self.con.cursor()
        condition = []
        param = []
        if filter_value:
            for key, val in filter_value.items():
                if key == "ticket_id":
                    condition.append("t.ticket_id = ?")
                    param.append(val)
                elif key == "branch_id":
                    condition.append("t.branch_id = ?")
                    param.append(val)
                elif key == "depart_id":
                    condition.append(" r.target_id = ? ")
                    param.append(val)
                elif key == "actor_id":
                    condition.append("t.actor_id = ? ")
                    param.append(val)
                elif key == "state_id":
                    condition.append("t.state_id = ?")
                    param.append(val)

        where_sql  = ""
        if condition:
            where_sql = " WHERE " + " AND ".join(condition)

        base_query = """SELECT t.ticket_id,
            t.code_ticket,
            t.severity,
            t.actor_id,
            t.branch_id,
            t.comment,
            s.status_name AS ticket_state,
            t.assigned_to,
            t.date_create,
            t.file_id,
            r.rule_name,
            b.branch_name
            FROM tickets AS t 
            JOIN rules AS r 
            ON r.code = t.code_ticket
            JOIN ticket_status AS s  
            ON t.state_id = s.status_id
            JOIN branch AS b
            ON t.branch_id = b.branch_id
            """
        request = base_query + where_sql
        try:
            rows = cur.execute(request, param).fetchall()
        except Error as e:
            raise RepositoryError(f"Error in get_tickets: {e}") from e
        tickets = [TicketView.for_db(dict(row)) for row in rows]
        return tickets


    def create(self, ticket: Ticket) -> int:
        cur = self.con.cursor()
        state_mapper = MapperState(self.con)
        state_id = state_mapper.get_state_id(ticket.state.name)
        cur.execute("""INSERT INTO tickets (
    code_ticket,
    severity,
    actor_id,
    branch_id,
    comment,
    state_id,
    assigned_to,
    file_id,
    date_create) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)""",
(ticket.code,
    ticket.context.severity.name,
    ticket.context.actor_id,
    ticket.context.branch_id,
    ticket.context.comment,
    state_id,
    ticket.assigned_to,
    ticket.context.file_id,
    ticket.date_create))
        return cur.lastrowid

    def update(self,
            ticket: Ticket,
            ) -> None:
        cur = self.con.cursor()
        state_mapper = MapperState(self.con)
        state_id = state_mapper.get_state_id(ticket.state.name)
        cur.execute("""UPDATE tickets SET
            state_id = (?),
            assigned_to = (?),
            comment = (?)
        WHERE ticket_id = ? """,
                    (state_id,
                     ticket.assigned_to,
                     ticket.context.comment,
                     ticket.id))
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
        cur.execute("""INSERT INTO history
                    (ticket_id, timestamp, user_id, field, old, new)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                    (ticket_id, timestamp, user_id, field, old, new)
                    )

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
