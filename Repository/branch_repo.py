from sqlite3 import Error
from typing import Optional
from core.exceptions import RepositoryError, IncorrectWrite
from logger.logger import core_logger
from repository.base import Repo


class BranchRepo(Repo):
    def get(self,
        filter_value: Optional[dict] = None)-> list[dict]:
        cur = self.con.cursor()
        base_query = """SELECT b.branch_id,
                                b.branch_name,
                                u.user_name AS branch_manager
                                FROM branch AS b
                                LEFT JOIN users AS u
                                ON b.branch_id = u.branch_id AND u.role_id = 2"""
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
        except Error as e :
            raise RepositoryError(f"Error in get_branch_with_data: {e}") from e

    def create(self,
              branch_name: str)->None:
        cur = self.con.cursor()
        cur.execute("INSERT INTO branch (branch_name) VALUES (?)",(branch_name,))

    def rename(self,
              branch_id: int,
              new_name: str)->None:
        cur = self.con.cursor()
        cur.execute('UPDATE branch SET branch_name = ? WHERE branch_id = ?',
                         (new_name, branch_id))
        if cur.rowcount == 0:
            core_logger.error('Branch not found')
            raise IncorrectWrite("Branch not found")

    def delete(self,
            branch_id: int)->None:
        cur = self.con.cursor()
        cur.execute('UPDATE branch SET branch_activity = 0 WHERE branch_id = ?', (branch_id,))
        if cur.rowcount == 0:
            core_logger.error("Branch not found")
            raise IncorrectWrite("Branch not found")

    def activate(self,
                branch_id:int)->None:
        cur = self.con.cursor()
        cur.execute('UPDATE branch SET branch_activity = 1 WHERE branch_id = ?', (branch_id,))
        if cur.rowcount == 0:
            core_logger.error("Branch not found")
            raise IncorrectWrite("Branch not found")
