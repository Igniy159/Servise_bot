from sqlite3 import Connection
from repository.branch_repo import BranchRepo
from repository.ticket_repo import TicketRepo
from repository.user_repo import UserRepo


class Repo:
    def __init__(self, con:Connection):
        self.con = con

class UoW:
    def __init__(self, con: Connection):
        self.tickets = TicketRepo(con)
        self.users = UserRepo(con)
        self.branches = BranchRepo(con)
        self.con = con

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.con.commit()
        else:
            self.con.rollback()
    def __call__(self):
        return self.con
