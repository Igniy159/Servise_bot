from sqlite3 import Connection
from typing import Optional
from repository.branch_repo import BranchRepo
from repository.create_migrations import get_connect
from repository.ticket_repo import TicketRepo
from repository.user_repo import UserRepo
from repository.mapper_repo import MapperRoles, MapperDepart

class UoW:
    def __init__(self, con: Connection):
        self.tickets = TicketRepo(con)
        self.users = UserRepo(con)
        self.branches = BranchRepo(con)
        self.dep_mapper = MapperDepart(con)
        self.role_mapper = MapperRoles(con)
        self.con = con

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.con.commit()
        else:
            self.con.rollback()

class UowFactory:
    def __init__(self, path: Optional[str]=None):
        self.path = path

    def __call__(self):
        return UoW(get_connect(self.path))
