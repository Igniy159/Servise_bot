
from UX_laier.translate import translate, union_history


def tr(config, key):
    dict_en_ru = config['translate']
    res = dict_en_ru.get(key, key)
    return res


def create_apply_ticket_msg(event_alert,config,send=None):
    msg = []
    if event_alert['action'] == "create_ticket" and event_alert['type'] != "ALERT":
        if send == 'self':
            msg = [f"Заявка #{event_alert['ticket_id']} создана."]
        elif send == "target":
            msg = [f"Создана новая заявка #{event_alert['ticket_id']}",
                   f"Филиал: {event_alert['branch_name']}",
                   f"Проблема: {tr(config, event_alert['problem_name'])}",
                   f" Тип проблемы: {tr(config, event_alert['problem_type'])}",
                   "Примите заявку в работу."]
        elif send == 'manager':
            msg = [f"Создана заявка #{event_alert['ticket_id']} в вашем филиале",
                   f"Проблема: {tr(config, event_alert['problem_name'])}",
                   f" Тип проблемы: {tr(config, event_alert['problem_type'])}",
                   f" Статус заявки: {tr(config, event_alert['current_state'])}",
                   "Если заявка НОВАЯ, вам нужно её подтвердить",
                   "Если заявка ПОДТВЕРЖДЕНА ничего делать не нужно"]

    elif event_alert['action'] == "create_ticket" and event_alert['type'] == "ALERT":
        if event_alert['scenario'] in ('CRITICAL_NOTIFICATION',"SECURITY_INCIDENT"):
            critical_alert = True
        else:
            critical_alert = False
        comment = event_alert.get('comment')
        if send == 'self':
            msg = ["Сообщение отправлено"]
        elif send == 'manager':
            msg = [f'Сообщение от вашего филиала:',
                   f"{tr(config, event_alert['problem_name'])}"]
            if comment:
                msg.append(comment)
        elif send == 'target':
            msg = [f"Сообщение от филиала:{event_alert['branch_name']}",
                   f"{tr(config, event_alert['problem_name'])}"]
            if comment:
                msg.append(comment)
        if critical_alert:
            msg.append("Данное сообщение является срочным!")

    elif event_alert['action'] == 'confirm':
        if send == 'self':
            msg = [f"Заявка #{event_alert['ticket_id']} подтверждена."]
        elif send == "target":
            msg = [f"Создана новая заявка #{event_alert['ticket_id']}",
                   f"Филиал: {event_alert['branch_name']}",
                   f"Проблема: {tr(config, event_alert['problem_name'])}",
                   f" Тип проблемы: {tr(config, event_alert['problem_type'])}",
                   "Примите заявку в работу."]

    elif event_alert['action'] == 'reject_comment':
        msg = [f"Заявка #{event_alert['ticket_id']} была отменена",
               f"Причина: {event_alert['reject_comment']}"]

    elif event_alert['action'] == 'change_priority':
        msg = [f"Заявка #{event_alert['ticket_id']}.",
               f"Изменен приоритет на {tr(config, event_alert['priority'])}"]

    elif event_alert['action'] == 'assigned_to':
        if send == 'self':
            msg = [f"Заявка #{event_alert['ticket_id']} успешно подтверждена"]
        elif send == 'manager':
            msg = [f"Заявка #{event_alert['ticket_id']} успешно подтверждена сотрудником {event_alert['assigned_to']}"]

    elif event_alert['action'] == 'on_off_external':
        msg = [f"Заявка #{event_alert['ticket_id']}",
               f"Переключена в статус {tr(config, event_alert['current_state'])}"]
        comment = event_alert.get('comment')
        if comment:
            msg.append(f"Причина: {comment}")

    elif event_alert["action"] == 'finish_ticket':
        if send == 'self':
            msg = [f"Работа по заявке #{event_alert['ticket_id']} завершена. Управляющий должен закрыть заявку"]
        elif send == 'manager':
            msg = [f"Работа по заявке #{event_alert['ticket_id']} завершена. Закройте заявку если работа выполнена",
                   "Если работа не сделана, не закрывайте заявку",
                   f'Если работа выполнена частично или некачественно, закройте заявку и откройте новую с комментарием']
    elif event_alert['action'] == 'close_ticket':
        if send == 'self':
            msg = [f"Заявка #{event_alert['ticket_id']} закрыта"]
        elif send == 'assign':
            msg = [f"Заявка #{event_alert['ticket_id']} закрыта. Благодарим за работу"]

    return '\n'.join(msg)


def branch_msg(event_alert,config):
    msg = ''
    if event_alert['action'] == 'create_branch':
        msg = f"Филиал {event_alert['branch_name']} успешно создан"
    elif event_alert['action'] == 'rename_branch':
        msg = f"Филиал успешно изменил имя на: {event_alert['branch_name']}"
    elif event_alert['action'] == 'receive_branch':
        msg = translate(event_alert['branches'],config)
    elif event_alert['action'] == 'delete_branch':
        msg = f"Филиал #{event_alert['branch_id']} успешно удалён"
    return msg


def user_msg(event_alert,config):
    msg = ''
    if event_alert['action'] == 'create_user':
        msg = f"Пользователь {event_alert['user_name']} успешно добавлен"
    elif event_alert['action'] == "delete_user":
        msg = f"Пользователь #{event_alert['user_id']} успешно удалён"
    elif event_alert['action'] == 'change_user':
        msg = f"Параметры пользователя {event_alert['user_name']} успешно изменены"
    elif event_alert['action'] == 'rename_user':
        msg = f"У пользователя изменилось имя на {event_alert['user_name']}"
    elif event_alert['action'] == "receive_user":
        msg = translate(event_alert['users'],config)
    return msg


def show_ticket_msg(event_alert,config):
    msg = ''
    if event_alert['action'] == 'receive_ticket':
        msg = translate(event_alert['tickets'],config)
    elif event_alert['action'] == 'receive_history':
        msg = union_history(event_alert['history'],config)
    return msg