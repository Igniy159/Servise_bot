from core.ticket_core import User


class Formatter:
    def __init__(self, raw_config: dict):
        self.dict_en_ru = raw_config['translate']

    def translate(self, key):
        return self.dict_en_ru.get(key, "")

    def user_formatter(self, user: User):
        user.role = self.translate(user.role.name)
        user.depart_name = self.translate(user.depart_name)
        return f"{user.name} | {user.role} | {user.depart_name or user.branch_name or " "}"


def tr(config, key):
    dict_en_ru = config['translate']
    res = dict_en_ru.get(key, key)
    return res

def translate_ticket(tickets: list[dict], config)-> str:
    dict_en_ru = config['translate']
    list_res = []
    for ticket in tickets:
        res = {}
        for key, value in ticket.items():
            if value is None:
                continue
            if key in dict_en_ru:
                res[dict_en_ru[key]] = value
        for key, value in res.items():
            if value in dict_en_ru:
                res[key] = dict_en_ru[value]
        list_res.append(res)

    msg = ''
    for key in list_res:
        msg += "\n".join([f"{k} {v}" for k, v in key.items()])
        msg += "\n" + '\n'
    return msg

def union_history(history: list,config)->str:
    dict_en_ru = config['translate']
    res = []
    write = None
    for patch in history:
        if write is None or patch['timestamp'] != write['timestamp']:
            if write:
                res.append(write)
            write = dict(user_name=patch["user_name"], role_name=dict_en_ru[patch['role_name']],
                             timestamp=patch["timestamp"], change={})
        if patch['new_value'] in dict_en_ru:
            patch['new_value'] = dict_en_ru[patch['new_value']]
        write["change"][patch["field"]] = patch["new_value"]
    if write:
        res.append(write)
    msg = ''

    for patch in res:
        msg += patch['timestamp'] + '\n'
        msg += patch['user_name'] + " " + patch['role_name'] + '\n'
        if patch['change'].get('current_state'):
            msg += 'Статус: '+ patch['change']['current_state'] + '\n'
        if patch['change'].get('comment'):
            msg += 'Комментарий: ' + patch['change']['comment'] + '\n'
        if patch['change'].get('reject_comment'):
            msg += 'Причина отмены: ' + patch['change']['reject_comment'] + '\n'
        if patch['change'].get('date_close'):
            msg += 'Время закрытия: ' + patch['change']['date_close'] + '\n'
        if patch['change'].get("priority"):
            msg += 'Приоритет изменен на: ' + patch['change']["priority"] + '\n'
        if patch['change'].get("assigned_to"):
            msg += 'Принял в работу: ' + patch['change']["assigned_to"] + '\n'
    return msg
