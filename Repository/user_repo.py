from sqlite3 import Error
from typing import Optional
from core.exceptions import RepositoryError, IncorrectWrite
from repository.unit_of_work import Repo


class UserRepo(Repo):

    def get(self,
    filter_value: Optional[dict]=None
    )-> list[dict]:
        cur = self.con.cursor()
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
        except Error as e:
            raise RepositoryError(f"Error in get_tickets: {e}") from e

    def create(self,
            user_name: str,
            api_user_id: int,
            role_id: int,
            depart_id: Optional[int]=None,
            branch_id: Optional[int]=None
            )-> int:
        cur = self.con.cursor()
        cur.execute(
            """INSERT INTO users (user_name, api_user_id, role_id, depart_id, branch_id)
             VALUES (?, ?, ?, ?, ?)""",
            (user_name, api_user_id, role_id, depart_id, branch_id))
        return cur.lastrowid

    def delete(self,
                      user_id: int
                      )->None:
        cur = self.con.cursor()
        cur.execute('UPDATE users SET user_activity = 0 WHERE user_id = ?', (user_id,))
        if cur.rowcount == 0:
            raise IncorrectWrite("User not found")

    def activate(self,
                      user_id: int)->None:
        cur = self.con.cursor()
        cur.execute('UPDATE users SET user_activity = 1 WHERE user_id = ?', (user_id,))
        if cur.rowcount == 0:
            raise IncorrectWrite("User not found")

    def update(self,
               user_id:int,
               role_id:int,
               branch_id:int,
               depart_id:int,
               )->None:
        cur = self.con.cursor()
        cur.execute("""UPDATE users SET role_id = ?, branch_id = ?, depart_id = ?
                    WHERE user_id = ?""", (role_id,branch_id,depart_id, user_id))
        if cur.rowcount == 0:
            raise IncorrectWrite("User not found")

    def rename(self,
            user_id:int,
             user_name:str,
            )-> None:
        cur = self.con.cursor()
        cur.execute("""UPDATE users SET user_name = ? WHERE user_id = ?""",
                         (user_name, user_id))
        if cur.rowcount == 0:
            raise IncorrectWrite("User not found")
