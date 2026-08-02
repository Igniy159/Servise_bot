from sqlite3 import Error
from typing import Optional
from core.exceptions import RepositoryError
from core.ticket_core import Alert, RuleAlert
from repository.base import Repo


class AlertRepo(Repo):
    def create(self,
               alert: Alert
              )->None:
        cur = self.con.cursor()
        cur.execute("""INSERT INTO alerts (
        code_alert,
        creator_id,
        branch_id,
        date_create,
        comment), VALUES (?,?,?,?,?,?)""",
                    (alert.code_alert,
                                alert.actor_id,
                               alert.branch_id,
                               alert.date_create,
                               alert.comment))
        return cur.lastrowid

    def get(self,
    filter_value: Optional[dict]=None
    )-> list[Alert]:
        cur = self.con.cursor()
        condition = []
        param = []
        if filter_value:
            for key, val in filter_value.items():
                if val is None:
                    continue
                if key == "alert_id":
                    condition.append("a.alert_id = ?")
                    param.append(val)
                elif key == "creator_id":
                    condition.append("a.creator_id = ?")
                    param.append(val)
                elif key == "branch_id":
                    condition.append("a.branch_id = ?")
                    param.append(val)
                elif key == "target_id":
                    condition.append("a.target_id = ?")
                    param.append(val)
        where_sql = ''
        if condition:
            where_sql = " WHERE " + " AND ".join(condition)
        base_query = """SELECT
                        a.creator_id,
                        a.branch_id,
                        a.date_create,
                        r.name_alert,
                        r.target_id
                        a.comment,
                        FROM alert AS a
                        JOIN rules_alert AS r
                        ON r.code_alert = a.code_alert"""
        request = base_query + where_sql
        try:
            rows = cur.execute(request, param).fetchall()
            return [Alert.for_db(dict(row)) for row in rows]
        except Error as e:
            raise RepositoryError(f"Error in get_alert: {e}") from e

    def get_rules(self,
                  filter_value: Optional[dict]=None)-> list[RuleAlert]:
        cur = self.con.cursor()
        condition = []
        param = []
        if filter_value:
            for key, val in filter_value.items():
                if val is None:
                    continue
                if key == "code_alert":
                    condition.append("r.code_alert = ?")
                    param.append(val)
                elif key == "class_alert":
                    condition.append("r.class_alert = ?")
                    param.append(val)
                elif key == "target_id":
                    condition.append("d.depart_id = ?")
                    param.append(val)
        where_sql = ''
        if condition:
            where_sql = " WHERE " + " AND ".join(condition)
        base_query = """
        SELECT 
        r.code_alert,
        r.class_alert,
        r.name_alert,
        d.depart_id AS target_id,
        d.depart_name AS target_name
        FROM rules_alert AS r
        JOIN department AS d
        ON d.depart_id = r.target_id """
        request = base_query + where_sql
        try:
            rows = cur.execute(request, param).fetchall()
            return [RuleAlert.for_db(dict(row)) for row in rows]
        except Error as e:
            raise RepositoryError(f"Error in get_alert: {e}") from e
