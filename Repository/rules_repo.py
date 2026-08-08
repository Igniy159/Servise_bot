from typing import Optional
from sqlite3 import Error
from core.exceptions import RepositoryError
from core.ticket_core import Rule
from repository.base import Repo


class RulesRepo(Repo):
    def get_rules(self,
                  filter_value: Optional[dict]=None)-> list[Rule]:
        cur = self.con.cursor()
        condition = []
        param = []
        if filter_value:
            for key, val in filter_value.items():
                if val is None:
                    continue
                if key == "kind":
                    condition.append("r.code = ?")
                    param.append(val)
                if key == "code":
                    condition.append("r.code = ?")
                    param.append(val)
                elif key == "class":
                    condition.append("r.class = ?")
                    param.append(val)
                elif key == "target_id":
                    condition.append("d.depart_id = ?")
                    param.append(val)
        where_sql = ''
        if condition:
            where_sql = " WHERE " + " AND ".join(condition)
        base_query = """
        SELECT 
        r.code,
        r.kind,
        r.class,
        r.name,
        d.depart_id AS target_id,
        d.depart_name AS target_name
        FROM rules AS r
        JOIN department AS d
        ON d.depart_id = r.target_id """
        request = base_query + where_sql
        try:
            rows = cur.execute(request, param).fetchall()
            return [Rule.for_db(dict(row)) for row in rows]
        except Error as e:
            raise RepositoryError(f"Error in get_rule: {e}") from e
