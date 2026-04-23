from Service.Common import transactional,filters_validator,filters_key_validator,apply_scope
from typing import Optional
from Core.Ticket_core import User
from Core.exceptions import PermissionDenied,ServiseValidationBreak, CoreValidationBreak,IncorrectWrite
from Core.Ticket_core import validate_event, resolve_decision,Ticket,has_permission
from Logger.logger import core_logger
from Repository.write_model import ticket_assert,insert_history_record,ticket_update
from Repository.read_model import get_users_with_data, get_tickets_with_data,fetch_history_ticket
from datetime import datetime

@transactional
def write_ticket(config:dict,
                 user: Optional[User],
                 event_data: dict,
                 con=None)-> dict:

    if not has_permission(user.role, "create_ticket", config):
        raise PermissionDenied(f" User {user['user_name']} cannot create ticket")

    if user.branch_id is None and 'branch_id' not in event_data:
        raise ServiseValidationBreak("if changed not branch: in event need field branch_id")

    try:
        validate_event(event_data, config)
    except CoreValidationBreak as e:
        core_logger.error(f"Event {event_data['problem_name']} incorrect. {e}")
        raise


    event_res = resolve_decision(event_data, config)

    solution = escalation(config,event_data, user, con=con)

    ticket = Ticket.from_created(event_res,config,user)
    ticket.update_solution(solution)
    state_for_history = ticket.current_state

    ticket_for_db = Ticket.for_data_base(ticket,config)

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

    api_recipient = solution['api_recipient']
    event_alert = {'branch_name': ticket.branch_name,
                   'problem_name': ticket.problem_name,
                   'self': user.api_id,
                   'target':api_recipient.get('target'),
                   'manager':api_recipient.get('manager'),
                   'problem_type': ticket.problem_type,
                   'ticket_id': ticket_id,
                   'branch_id': ticket.branch_id,
                   'current_state': state_for_history,
                   'action': 'create_ticket',
                   'comment': ticket.comment,
                   'type': ticket.event_type,
                   'scenario': ticket.scenario}
    return event_alert

@transactional
def escalation(config:dict,
               event_data:dict,
               user: Optional[User],
               con=None):
    manager = get_users_with_data(filter_value={'user_activity': 1, 'role_id': 2, 'branch_id': user.branch_id},con=con)
    owner = get_users_with_data(filter_value={'user_activity': 1,'role_id': 4},con=con)
    depart = get_users_with_data(filter_value={'user_activity': 1, 'role_id': 3, 'depart_id': event_data['target']})
    need_confirm = config['scenarios']['SCENARIOS'][event_data['scenario']]["confirmation_required"]
    solution ={}

    if not depart and not manager:
        solution['assigned_to'] = owner[0]['user_id']
        solution['target'] = 'TOP_MANAGEMENT'
        solution['current_state'] = "IN_PROGRESS"
        solution['api_recipient']['target'] = (owner[0]['api_user_id'])

    elif not depart and manager and need_confirm:
        solution['target'] = 'TOP_MANAGEMENT'
        solution['current_state'] = "NEW"
        solution['api_recipient']['manager'] = manager[0]['api_user_id']

    elif not depart and manager and not need_confirm:
        solution['target'] = 'TOP_MANAGEMENT'
        solution['current_state'] = "CONFIRMED"
        solution['api_recipient']['manager'] = manager[0]['api_user_id']
        solution['api_recipient']['target'] = [users['api_user_id'] for users in depart]

    elif not manager and depart:
        solution['current_state'] = "CONFIRMED"
        solution['api_recipient']['target'] = [users['api_user_id'] for users in depart]

    elif manager and depart:
        solution['current_state'] = "NEW"
        solution['api_recipient']['manager'] = manager[0]['api_user_id']

    return solution

@transactional
def apply_write_patch(config:dict, user:Optional[User], patch: dict, ticket_id: int, flag: str, con=None)-> dict:
    if user.role == 'OWNER':
        type_fsm = config['ticket_lifecycle']['ADMIN_LIFECYCLE']
    else:
        type_fsm = config['ticket_lifecycle']['NORMAL_LIFECYCLE']

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
def receive_tickets(user:Optional[User], size=None, filters=None,con=None)-> list[dict]:
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
def receive_history(user:Optional[User], ticket_id, config, con=None):
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