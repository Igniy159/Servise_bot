from typing import Optional
from core.exceptions import IncorrectWrite
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

    def get_all_depart(self)->list[dict]:
        cur = self.con
        res = cur.execute("""SELECT d.depart_id, d.depart_name
                        FROM department AS d""").fetchall()
        return [dict(row) for row in res]

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
