from service.common import transactional,filters_validator,filters_key_validator,apply_scope
from core.ticket_core import User
from core.exceptions import PermissionDenied,ServiseValidationBreak, CoreValidationBreak,IncorrectWrite
from core.ticket_core import Ticket
from policy.policy_ticket import PolicyObject, PolicyRequest, PolicyAlert
from logger.logger import core_logger
from repository.write_model import ticket_assert,insert_history_record,ticket_update
from repository.read_model import get_users_with_data, get_tickets_with_data, fetch_history_ticket, get_branch_with_data
from datetime import datetime
from api.command import (CmdCreateTicket, CmdCloseTicket, CmdAssignTicket, CmdFinishTicket,
CmdRejectTicket,CmdPriorityTicket,CmdConfirmTicket, CmdOnWaitingTicket,
CmdOffWaitingTicket, QueryGetTicket, QueryGetHistoryTicket)


@transactional
def write_ticket(user: User,
                cmd: CmdCreateTicket,
                config: dict,
                con=None)-> tuple:
#Определяем тип события
    type_event = type_resolver(cmd,config['enum'])
    if type_event == "OBJECT_PROBLEM":
        event_control =  PolicyObject(user,cmd,config)
    elif type_event == "REQUEST":
        event_control = PolicyRequest(user,cmd,config)
    else:
        event_control = PolicyAlert(user,cmd,config)
#Валидируем команду и принимаем решение (сценарий, отдел, приоритет)
    try:
        resolve = event_control.policy_cmd()
    except CoreValidationBreak as e:
        core_logger.error(f"Event {cmd['problem_name']} incorrect. {e}")
        raise
    except PermissionDenied as e:
        core_logger.error(f"Error in access user: {e}")
        raise
    if cmd.branch_id:
        resolve['branch_name'] = get_branch_with_data(
                                {'branch_id': cmd.branch_id},con=con
                                )[0]['branch_name']
#Собираем контекст из БД
    manager = get_users_with_data({'user_activity': 1,
                                   'role_id': 2,
                                   'branch_id': user.branch_id},
                                  con=con)
    owner = get_users_with_data({'user_activity': 1,
                                 'role_id': 4},
                                con=con)
    depart = get_users_with_data({'user_activity': 1,
                                  'role_id': 3,
                                  'depart_id': resolve['target_id']})
    context = {'manager': manager,
                'owner': owner,
                'depart':depart}
#Собираем из контекста правила эскалации(отдел, текущий статус, получателей)
    solution, recipient = escalation(config['scenarios'],cmd,context)
#Создаём тикет
    ticket = Ticket.from_created(cmd,resolve,config,user)
    ticket.update_solution(solution)
    state_for_history = ticket.current_state
    ticket_for_db = Ticket.for_data_base(ticket,config)
#Записываем тикет и историю в БД
    try:
        ticket_id = ticket_assert(ticket_for_db, con=con)
    except IncorrectWrite as e:
        core_logger.error(f"Ticket has not write. Reason: {e}")
        raise

    try:
        insert_history_record(ticket_id,
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              user.id,
                              'current_state',
                              None,
                              state_for_history, con=con)
    except IncorrectWrite as e:
        core_logger.error(f"History has not write. Reason: {e}")
        raise
#Формируем событие и ответ для API
    recipient['self'] = user.api_id
    event_alert = {'branch_name': ticket.branch_name,
                   'problem_name': ticket.problem_name,
                   'problem_type': ticket.problem_type,
                   'ticket_id': ticket_id,
                   'branch_id': ticket.branch_id,
                   'current_state': state_for_history,
                   'action': 'create_ticket',
                   'comment': ticket.comment,
                   'type': ticket.event_type,
                   'scenario': ticket.scenario}
    return event_alert, recipient


def type_resolver(cmd:CmdCreateTicket, enums:dict)->str:
    """The function determines the event type through the config and returns it as a string"""
    type_event = ""
    if cmd.problem_category in enums['zones']:
        type_event = ' OBJECT_PROBLEM'
    elif cmd.problem_category in enums['REQUEST_CATEGORY']:
        type_event = 'REQUEST'
    elif cmd.problem_category in enums['CATEGORY_ALERTS']:
        type_event = 'ALERT'
    return type_event


def escalation(scenarios: dict,
               cmd: CmdCreateTicket,
               context: dict)-> tuple:

    need_confirm = scenarios['SCENARIOS'][cmd['scenario']]["confirmation_required"]
    solution ={}
    recipient = {}

    if not context['depart'] and not context['manager']:
        solution['assigned_to'] = context['owner'][0]['user_id']
        solution['target'] = 'TOP_MANAGEMENT'
        solution['current_state'] = "IN_PROGRESS"
        recipient['target'] = context['owner'][0]['api_user_id']

    elif not context['depart'] and context['manager'] and need_confirm:
        solution['target'] = 'TOP_MANAGEMENT'
        solution['current_state'] = "NEW"
        recipient['manager'] = context['manager']['api_user_id']

    elif not context['depart'] and context['manager'] and not need_confirm:
        solution['target'] = 'TOP_MANAGEMENT'
        solution['current_state'] = "CONFIRMED"
        recipient['manager'] = context['manager'][0]['api_user_id']
        recipient['target'] = [users['api_user_id'] for users in context['depart']]

    elif not context['manager'] and context['depart']:
        solution['current_state'] = "CONFIRMED"
        recipient['target'] = [users['api_user_id'] for users in context['depart']]

    elif context['manager'] and context['depart']:
        solution['current_state'] = "NEW"
        recipient['manager'] = context['manager'][0]['api_user_id']

    return solution, recipient

@transactional
def apply_write_patch(user: User,
                      cmd ,
                      flag: str,
                      con)-> dict:
    if user.role == 'OWNER':
        type_fsm = config['ticket_lifecycle']['ADMIN_LIFECYCLE']
    else:
        type_fsm = config['ticket_lifecycle']['NORMAL_LIFECYCLE']

    # patch = {'current_state': 'CONFIRMED',
    #          'comment': comment}
    # patch = {'current_state': 'CANCELLED',
    #          'reject_comment': reject_comment,
    #          'date_close': datetime.now()}
    # patch = {"priority": new_priority_id,
    #          'comment': comment}
    # patch = {'current_state': 'IN_PROGRESS',
    #          'assigned_to': self.user.id,
             # 'comment': comment}
    # patch = {'current_state': 'WAITING_EXTERNAL',
    #          'comment': comment}
    # patch = {'current_state': 'IN_PROGRESS',
    #          'comment': comment}
    # patch = {'current_state': 'RESOLVED',
    #          'comment': comment}
    # patch = {'current_state': 'CLOSED',
    #          'comment': comment,
    #          'date_close': datetime.now()}


    if not has_permission(user.role, flag, config):
        raise PermissionDenied(f" User {user.name} cannot apply {flag}")

    ticket = get_tickets_with_data({"ticket_id": ticket_id}, con=con)
    if ticket:
        ticket = Ticket(ticket[0])
    else:
        raise ServiseValidationBreak("Ticket not found")
    dep_name = ticket.target

    if user.branch_name is not None and user.branch_name != ticket.branch_name:
        raise PermissionDenied(" User action only mine branch_ticket")

    updated_ticket = ticket.update_ticket(config, patch, user, type_fsm)
    ticket_update(updated_ticket,con=con)
    for record in updated_ticket.history:
        insert_history_record(ticket_id,
                            record['timestamp'],
                            user.id,
                            record['changes'],
                            record['old'],
                            record['new'], con=con)
    ticket.history.clear()


    event_alert = {}
    target = []
    manager = []
    assig = []
    users = get_users_with_data({'activity': 1},con=con)
    for key in users:
        if dep_name and key['depart_name'] == dep_name:
            target.append(key['api_user_id'])
        elif key['branch_name'] == ticket.branch_name and key['role_name'] == "MANAGER":
            manager.append(key['api_user_id'])
        elif flag == 'assigned_to' or key['user_id'] == ticket.assigned_to:
            assig.append(key['api_user_id'])
            event_alert['assigned_to'] = key['user_name']    #this name for message


    event_alert['target'] = target
    event_alert['action'] = flag
    event_alert['ticket_id'] = ticket_id
    event_alert['priority'] = patch.get('priority')
    event_alert['comment'] = patch.get('comment')
    event_alert['reject_comment'] = patch.get('reject_comment')
    event_alert['current_state'] = patch.get('current_state')
    event_alert['self'] = user.api_id
    event_alert['manager'] = manager
    event_alert['assigned'] = assig       #this sends api_user_id


    return event_alert

@transactional
def receive_tickets(user:User,
                    cmd: QueryGetTicket,
                    con)-> list[dict]:
    if filters:
        filters_key_validator(filters)
    filters_validator(user, filters)
    filters = apply_scope(user, filters)
    tickets = get_tickets_with_data(filters, con=con)
    res = []
    if tickets:
        for ticket in tickets:
            if size == 'full':
                res.append(full_view(ticket, user['role_name']))
            else:
                res.append(short_view(ticket))
    return res

@transactional
def receive_history(user:User,
                    cmd: QueryGetHistoryTicket,
                    config:dict,
                    con):
    has_permission(user['role_name'],"history_vision",config)
    ticket = get_tickets_with_data({'ticket_id':ticket_id},con=con)[0]
    if user['branch_id'] is not None:
        if ticket['branch_id'] != user['branch_id']:
            raise PermissionDenied('User can show history only mine branch')
    return fetch_history_ticket(ticket_id,con=con)

#Маски
def full_view(ticket:dict, role: str):    #Построить модель для определенной роли
    ticket_view = {}
    role_field = {'OWNER': {"ticket_id",'creator_name','branch_name',"problem_name",'problem_type',
                              'zone','target','date_create','sla_reaction_deadline',
                              'sla_resolution_deadline','current_state','date_close', "assigned_to",'reject_comment',
                              'comment','priority'},
                    "SPECIALIST": {"ticket_id",'branch_name',"problem_name",'problem_type',
                              'zone','current_state','date_create','date_close', "assigned_to",
                              'comment','priority'},
                    "MANAGER": {"ticket_id",'creator_name',
                              'zone','date_create','date_close','comment','priority',"current_state"},
                    "EMPLOYEE": {"ticket_id","problem_name",'problem_type','zone','date_create',"current_state"}}
    need_field = role_field[role]
    for key, val in ticket.items():
        if key in need_field:
            ticket_view[key] = val
    return ticket_view

def short_view(ticket: dict):
    need_field = {'ticket_id','date_create','branch_name','priority', "problem_name", "current_state"}
    ticket_view = {}
    for key, val in ticket.items():
        if key in need_field:
            ticket_view[key] = val
    return ticket_view