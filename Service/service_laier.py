from Core.exceptions import *
from Logger.logger import core_logger
from Repository.create_migrations import get_connect,sq
from Repository.write_model import (ticket_assert, insert_history_record, update_user_params,
                                    user_soft_del, user_activate, user_assert, ticket_state,
                                    close_ticket, branch_activate, branch_rename, branch_soft_del, branch_assert,
                                    assign_ticket, change_priority, update_comment, reject_ticket, update_user_name)
from Repository.read_model import encode_object, get_users_with_data, get_tickets_with_data, get_branch_with_data, \
 fetch_history_ticket
from Core.Ticket_core import has_permission,create_ticket,update_ticket,User,Ticket, Branch
from datetime import datetime
from Core.loader import config
from typing import Optional


def transactional(func):
    def wrapper(*args, **kwargs):
        external_con = kwargs.get("con")
        con = external_con or get_connect()

        try:
            kwargs["con"] = con
            result = func(*args, **kwargs)
            if not external_con:
                con.commit()
            return result


        except AppError:
            if not external_con:
                con.rollback()
            raise

        except sq.Error as e:
            if not external_con:
                con.rollback()
            raise IncorrectWrite(str(e))

        finally:
            if not external_con:
                con.close()

    return wrapper
# CREATE - APPLY -DELETE operations
@transactional
def write_ticket(config:dict,
                 user: Optional[User],
                 event_data: dict,
                 con=None)-> dict:

    if not has_permission(user.role, "create_ticket", config):
        raise PermissionDenied(f" User {user['user_name']} cannot create ticket")

    if user.branch_id is None and 'branch_id' not in event_data:
        raise ServiseValidationBreak(f"if changed not branch: in event need field branch_id")

    solution = escalation(event_data, config, con=con)

    ticket = create_ticket(config, event_data, user)
    ticket.update_solution(solution)
    state_for_history = ticket.current_state

    ticket_for_db = Ticket.for_data_base(ticket,config)

    ticket_id = ticket_assert(ticket_for_db, con=con)

    insert_history_record(ticket_id,
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                          user.id,
                          'current_state',
                          None,
                          state_for_history, con=con)

    api_recipient = solution['api_recipient']
    event_alert = {'branch_name': user.branch_name,
                   'problem_name': ticket['problem_name'],
                   'self': user.api_id,
                   'target':api_recipient.get('target'),
                   'manager':api_recipient.get('manager'),
                   'problem_type': ticket.get('problem_type'),
                   'ticket_id': ticket_id,
                   'branch_id': ticket['branch_id'],
                   'current_state': state_for_history,
                   'action': 'create_ticket',
                   'comment': ticket.get('comment'),
                   'type': ticket.get('event_type'),
                   'scenario': ticket.get('scenario')}
    return event_alert

@transactional
def apply_write_path(config, user, patch: dict, ticket_id: int,flag: str,con=None)-> dict:
    if user['role_name'] == 'OWNER':
        type_fsm = config['ticket_lifecycle']['ADMIN_LIFECYCLE']
    else:
        type_fsm = config['ticket_lifecycle']['NORMAL_LIFECYCLE']

    if not has_permission(user['role_name'], flag, config):
        raise PermissionDenied(f" User {user['user_name']} cannot apply {flag}")

    ticket = get_tickets_with_data({"ticket_id": ticket_id}, con=con)
    if not ticket:
        raise ServiseValidationBreak("Ticket not found")
    else:
        ticket = ticket[0]
    dep_name = ticket.get('target')

    if user['branch_name'] is not None and user['branch_name'] != ticket['branch_name']:
        raise PermissionDenied(f" User action only mine branch_ticket")
    if ticket['assigned_to'] and flag == 'assigned_to':
        raise PermissionDenied(f"Ticket assigned another changed")
    path_func = {'current_state': ticket_state,
                 'date_close': close_ticket,
                 'assigned_to': assign_ticket,
                 'priority': change_priority,
                 'comment': update_comment,
                 'reject_comment': reject_ticket
                 }
    if "priority" in patch:
        priority_map = config['enum']['priority']
        for i, k in priority_map.items():
            if k == patch['priority']:
                patch['priority'] = i
    ticket = update_ticket(config, ticket, patch, user['role_name'], type_fsm)
    patch = encode_object(patch,config,con=con)

    for field, value in patch.items():
        if field not in path_func:
            continue
        func = path_func[field]
        func(ticket_id, value, con=con)
    for i in ticket['history']:
        insert_history_record(ticket_id, i['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                              user['user_id'], i['changes'], i['old'], i['new'], con=con)
    ticket['history'].clear()


    event_alert = {}
    target = []
    manager = []
    assig = []
    users = get_users_with_data({'activity': 1},con=con)
    for key in users:
        if dep_name and key['depart_name'] == dep_name:
            target.append(key['api_user_id'])
        elif key['branch_name'] == ticket['branch_name'] and key['role_name'] == "MANAGER":
            manager.append(key['api_user_id'])
        elif flag == 'assigned_to' or key['user_id'] == ticket.get('assigned_to'):
            assig.append(key['api_user_id'])
            event_alert['assigned_to'] = key['user_name']    #this name for message


    event_alert['target'] = target
    event_alert['action'] = flag
    event_alert['ticket_id'] = ticket_id
    event_alert['priority'] = patch.get('priority')
    event_alert['comment'] = patch.get('comment')
    event_alert['reject_comment'] = patch.get('reject_comment')
    event_alert['current_state'] = patch.get('current_state')
    event_alert['self'] = user['api_user_id']
    event_alert['manager'] = manager
    event_alert['assigned'] = assig       #this sends api_user_id


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
def lead_branches(user, action: str, config, name=None, branch_id=None, filters= None, con= None):
    if not has_permission(user['role_name'], "lead_branch",config):
        core_logger.error(f"This changed {user['user_name']} cannot use branch action")
        raise PermissionDenied(f'This changed {user['user_name']} cannot use branch action')
    event_alert = {'action': action}
    if action == "create_branch":
        if not name or not name.strip():
            core_logger.error("Name cannot be empty")
            raise ServiseValidationBreak("Name cannot be empty")
        branch = get_branch_with_data(filter_value={"branch_name": name}, con=con)
        if branch:
            branch = branch[0]
            branch_activate(branch['branch_id'], con=con)
        else:
            branch_assert(name, con=con)
        event_alert['branch_name'] = name


    elif action == "rename_branch":
        if not name or not name.strip():
            core_logger.error("Name cannot be empty")
            raise ServiseValidationBreak("Name cannot be empty")
        branch_rename(branch_id, name, con=con)
        event_alert['branch_name'] = name


    elif action == "receive_branch":
        branches = receive_branch(user, filters=filters, con=con)
        event_alert['branches'] = branches


    elif action == 'delete_branch':
        branch_soft_del(branch_id, con=con)
        event_alert['branch_id'] = branch_id

    else:
        core_logger.error("incorrect type action")
        raise ServiseValidationBreak("incorrect type action")
    event_alert['self'] = user['api_user_id']
    return event_alert


@transactional
def create_first_owner(name:str,api_user_id:int,config,con=None):
    if not name or not name.strip():
        raise ServiseValidationBreak("Name cannot be empty")
    existing_owner = get_users_with_data(
        filter_value={'role_name': 'OWNER'},
        con=con)
    if existing_owner:
        raise ServiseValidationBreak("Owner already exists")
    role = config['enum']['ROLES']['OWNER']
    return user_assert(name,api_user_id,role_id=role,con=con)

@transactional
def create_user(user:dict,
                name: str,
                api_user_id: int,
                role_id:int,
                depart_id=None, branch_id=None, con=None):
    if not name or not name.strip():
        raise ServiseValidationBreak("Name cannot be empty")
    created_user = {}
    chek_user = get_users_with_data(filter_value={"api_user_id": api_user_id}, con=con)
    if chek_user:
        return user_activate(chek_user[0]['api_user_id'], con=con)
    else:
        if user['role_name'] == "MANAGER":
            created_user['branch_id'] = user['branch_id']  # manager can assert only mine branch
            created_user['role_id'] = config['enum']['ROLES']['EMPLOYEE']  # manager assert only new employee
            created_user['depart_id'] = None
        elif user['role_name'] == "OWNER":
            created_user['branch_id'] = branch_id
            created_user['role_id'] = role_id
            created_user['depart_id'] = depart_id
        created_user = normalise_user(created_user, config)
    user_assert(name, api_user_id, role_id, depart_id=created_user['depart_id'], branch_id=created_user['branch_id'], con=con)
    event_alert = {'action': 'create_user','user_name': name,"self": user['api_user_id']}
    return event_alert

@transactional
def delete_user(user=None, user_id=None, con=None):
    event_alert = {'action': 'delete_user', 'user_id': user_id, "self": user['api_user_id']}
    if user['role_name'] == "MANAGER":
        deletable = get_users_with_data({"branch_id": user["branch_id"],
                                              'role_name': "EMPLOYEE",
                                              'user_id': user_id}, con=con)
        if deletable:
            user_soft_del(user_id, con=con)
            return event_alert
        else:
            raise PermissionDenied('User cannot delete')
    user_soft_del(user_id, con=con)
    return event_alert

@transactional
def change_user(user,user_id:int, role_id:int, depart_id=None, branch_id=None, con=None):
    users= get_users_with_data(filter_value={'user_id': user_id},con=con)
    if not users:
        core_logger.error(f'User not found')
        raise ServiseValidationBreak(f'User not found')
    changed = users[0]

    changed['role_id'] = role_id

    changed['depart_id'] = depart_id
    changed['branch_id'] = branch_id
    changed = normalise_user(changed, config)
    update_user_params(user_id, changed['role_id'], changed['branch_id'], changed['depart_id'], con=con)

    event_alert = {'action': 'change_user','user_name': changed['user_name'],"self": user['api_user_id']}
    return event_alert

@transactional
def rename_user(user,user_id:int, user_name:str,con=None):
    users= get_users_with_data(filter_value={'user_id': user_id},con=con)
    if not users:
        core_logger.error(f'User not found')
        raise ServiseValidationBreak(f'User not found')
    update_user_name(user_id,user_name,con=con)
    event_alert = {'action': 'rename_user','user_name': user_name,"self": user['api_user_id']}
    return event_alert

# READ operations
@transactional
def receive_tickets(user:dict, size=None, filters=None,con=None):
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
def receive_branch(user:dict, filters=None, con=None):
    if filters:
        filters_key_validator(filters)
    filters_validator(user, filters)
    filters = apply_scope(user, filters)
    res = get_branch_with_data(filters, con=con)
    return res

@transactional
def receive_user(user:dict,filters= None,con=None):
    if filters:
        filters_key_validator(filters)
    filters_validator(user, filters)
    filters = apply_scope(user, filters)
    res = get_users_with_data(filter_value=filters, con=con)
    event_alert = {'self': user['api_user_id'],"users": res, 'action': 'receive_user'}
    return event_alert

@transactional
def receive_history(user:dict, ticket_id, config, con=None):
    has_permission(user['role_name'],"history_vision",config)
    ticket = get_tickets_with_data({'ticket_id':ticket_id},con=con)[0]
    if user['branch_id'] is not None:
        if ticket['branch_id'] != user['branch_id']:
            raise PermissionDenied('User can show history only mine branch')
    return fetch_history_ticket(ticket_id,con=con)

#валидация фильтров
def filters_key_validator(filters: dict):
    if not isinstance(filters,dict):
        raise ServiseValidationBreak(f"this filters incorrect type")
    branch_key = {"branch_id", "branch_name", "branch_activity"}
    user_key = {"user_id","api_user_id","user_branch_id","user_depart_id","role_id","user_activity"}
    ticket_key = {"ticket_id","zone","branch_id","depart_id","creator_id","status","priority", 'state','sort_priority',"sort_status"}
    prohibit_keys = branch_key | user_key | ticket_key
    type_map ={"branch_id": int,
               "branch_name": str,
               "branch_activity": int,
               "user_id": int,
               "api_user_id": int,
               "user_branch_id": int,
                "user_depart_id": int,
               "role_id": int,
               "user_activity": int,
               "ticket_id": int,
               'zone': str,
               "depart_id": int,
               "creator_id": int,
               "status": int,
               "priority": int,
               'state': str,
               'sort_priority': str,
               "sort_status": str
    }
    for key, val in filters.items():
        if key not in prohibit_keys:
            raise ServiseValidationBreak(f"this key {key} not in prohibit_keys")
        elif not isinstance(val,type_map[key]):
            raise ServiseValidationBreak(f"This {val} incorrect type for {key}")
        elif key in ("user_activity", "branch_activity") and  val not in (0,1):
            raise ServiseValidationBreak(f"This {val} incorrect value for {key}")
        elif key in ('sort_priority', "sort_status") and  val not in ('asc','desc'):
            raise ServiseValidationBreak(f"This {val} incorrect value for {key}")
    return None
def apply_scope(user, filters):
    scoped = dict(filters or {})
    if user["role_name"] == "MANAGER":
        scoped["branch_id"] = user["branch_id"]
        scoped["user_branch_id"] = user["branch_id"]

    if user["role_name"] == "SPECIALIST":
        scoped["depart_id"] = user["depart_id"]

    if user["role_name"] == "EMPLOYEE":
        scoped["creator_id"] = user["user_id"]

    return scoped
def filters_validator(user:dict, filters= None):
    white_list_manager = ("branch_id","user_branch_id","user_activity",'ticket_id','state','sort_status')
    white_list_specialist =("ticket_id","zone","branch_id","depart_id","status","priority",'state','sort_priority',"sort_status")
    white_list_employee = ("creator_id","sort_status")
    if user['role_name'] == "OWNER":
        return None
    elif user['role_name'] == "MANAGER":
        if filters is None:
            raise PermissionDenied(f"MANAGER must have filter on data ")
        for key in filters:
            if key not in white_list_manager:
                raise PermissionDenied(f"Incorrect {key} value for MANAGER")
            elif key == "user_branch_id" and user["branch_id"] != filters["user_branch_id"]:
                raise PermissionDenied(f"Manager can view only mine branch")
            elif key == "branch_id" and user["branch_id"] != filters["branch_id"]:
                raise PermissionDenied(f"Manager can view only mine branch")
    elif user['role_name'] == "SPECIALIST":
        if filters is None:
            raise PermissionDenied(f"SPECIALIST must have filter on data ")
        for key in filters:
            if key not in white_list_specialist:
                raise PermissionDenied(f"Incorrect {key} value for SPECIALIST")
            elif key == "depart_id" and user["depart_id"] != filters["depart_id"]:
                raise PermissionDenied(f"Specialist can view only mine departament")
    elif user['role_name'] == "EMPLOYEE":
        if filters is None:
            raise PermissionDenied(f"EMPLOYEE must have filter on data ")
        for key in filters:
            if key not in white_list_employee:
                raise PermissionDenied(f"Incorrect {key} value for Employee")
            elif key == "creator_id" and user["user_id"] != filters["creator_id"]:
                raise PermissionDenied(f"EMPLOYEE can view only mine tickets")
    return None

def check_user(api_user_id:int,con=None)-> tuple|bool:
    con = con or get_connect()
    with con:
        res = get_users_with_data({'api_user_id':api_user_id,
                                   'user_activity': 1},con=con)
    return res[0] if res else None
def normalise_user(user:dict,config):
    roles = config['enum']['ROLES']
    role_name = ""
    for i, k in roles.items():
        if k == user['role_id']:
            role_name = i

    need_field = config['roles']['ROLES'][role_name]['required_field']
    if not need_field['branch_id']:
        user['branch_id'] = None
    if not need_field['depart_id']:
        user['depart_id'] = None
    for field, is_required in need_field.items():
        if is_required and not user.get(field):
            raise PermissionDenied(f" {role_name} requires {field}")
    return user
def chek_permission(user:dict,action:str,config,user_id=None):
    if not has_permission(user['role_name'],action,config):
        core_logger.error(f'This changed {user['user_id']} cannot use this {action}')
        raise PermissionDenied('This changed cannot use changed action')
    if user_id and user['user_id'] == user_id:
        core_logger('User cannot use self action')
        raise PermissionDenied('User cannot use self action')




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
def short_view(ticket:dict):
    need_field = {'ticket_id','date_create','branch_name','priority', "problem_name", "current_state"}
    ticket_view = {}
    for key, val in ticket.items():
        if key in need_field:
            ticket_view[key] = val
    return ticket_view





