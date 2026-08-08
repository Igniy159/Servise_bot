from typing import Optional
from core.exceptions import IncorrectWrite
from core.ticket_core import Department
from repository.base import Repo

class MapperDepart(Repo):
    def get_depart_id(self, name: str)-> Optional[int]:
        cur = self.con
        res = cur.execute("""SELECT d.depart_id
                        FROM department AS d
                        WHERE d.depart_name == ? """,(name,)).fetchone()
        if res:
            return res[0]
        raise IncorrectWrite("Department not found")
    def get_depart_name(self, dep_id: int)->  Optional[str]:
        cur = self.con
        res = cur.execute("""SELECT d.depart_name
                        FROM department AS d
                        WHERE d.depart_id == ? """, (dep_id,)).fetchone()
        if res:
            return res[0]
        raise IncorrectWrite("Department not found")

    def get_all_depart(self)->list[Department]:
        cur = self.con
        res = cur.execute("""SELECT d.depart_id, d.depart_name
                        FROM department AS d""").fetchall()
        return [Department.for_db(dict(row)) for row in res]

class MapperRoles(Repo):

    def get_roles_id(self, name: str)-> Optional[int]:
        cur = self.con
        res = cur.execute("""SELECT r.role_id
                        FROM role AS r
                        WHERE r.role_name == ? """,(name,)).fetchone()
        if res:
            return res[0]
        raise IncorrectWrite("Role not found")

    def get_roles_name(self, role_id: int)->  Optional[str]:
        cur = self.con
        res = cur.execute("""SELECT r.role_name
                        FROM role AS r
                        WHERE r.role_id == ? """, (role_id,)).fetchone()
        if res:
            return res[0]
        raise IncorrectWrite("Role not found")

class MapperState(Repo):

    def get_state_id(self, name: str)-> Optional[int]:
        cur = self.con
        res = cur.execute("""SELECT t.status_id
                        FROM ticket_status AS t
                        WHERE t.status_name == ? """,(name,)).fetchone()
        if res:
            return res[0]
        raise IncorrectWrite("Role not found")

    def get_state_name(self, state_id: int)->  Optional[str]:
        cur = self.con
        res = cur.execute("""SELECT t.status_name
                        FROM ticket_status AS t
                        WHERE t.status_name == ? """, (state_id,)).fetchone()
        if res:
            return res[0]

        raise IncorrectWrite("Role not found")