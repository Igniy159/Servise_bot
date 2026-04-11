
from datetime import datetime



#overdue ticket None -> state open + overdue ticket
def get_overdue_tickets(con=None):
    now = datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    cur = con.cursor()
    rows = cur.execute("""SELECT 
                        t.ticket_id,
                        t.creator_id,
                        u.user_name AS creator_name,
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
                       JOIN users AS u ON t.creator_id = u.user_id
                       JOIN role AS r ON u.role_id = r.role_id
                       LEFT JOIN department AS d ON d.depart_id = u.depart_id
                       LEFT JOIN branch AS b ON b.branch_id = u.branch_id
                       JOIN ticket_status AS st ON t.current_state = st.status_id
                       LEFT JOIN users AS asig ON t.assigned_to = asig.user_id
                       JOIN priority AS p ON t.priority = p.priority_id
                       
                       WHERE st.state == 'open' AND
                       t.sla_resolution_deadline IS NOT NULL AND
                        t.sla_resolution_deadline < ? 
                       
                       ORDER BY t.date_create ASC """, (now,))
    results = [dict(row) for row in rows]
    for res in results:
        res['date_create'] = datetime.strptime(res['date_create'], "%Y-%m-%d %H:%M:%S")
        res['sla_reaction_deadline'] = datetime.strptime(res['sla_reaction_deadline'], "%Y-%m-%d %H:%M:%S") if res[
            'sla_reaction_deadline'] else None
        res['sla_resolution_deadline'] = datetime.strptime(res['sla_resolution_deadline'], "%Y-%m-%d %H:%M:%S") if res[
            'sla_resolution_deadline'] else None
        res['date_close'] = datetime.strptime(res['date_close'], "%Y-%m-%d %H:%M:%S") if res['date_close'] else None
        res['history'] = []
    return results



#metrix ticket -> start_data + final_data(if final == None, get now)
#return tickets