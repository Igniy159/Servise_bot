from Service.Common import transactional,filters_key_validator,filters_validator,apply_scope
from Core.Ticket_core import has_permission
from Core.exceptions import PermissionDenied,ServiseValidationBreak
from Logger.logger import core_logger
from Repository.write_model import user_assert,user_activate,user_soft_del,update_user_params,update_user_name
from Repository.read_model import get_users_with_data


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
                config:dict,
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
def change_user(user,user_id:int, role_id:int,config, depart_id=None, branch_id=None, con=None):
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


@transactional
def receive_user(user:dict,filters= None,con=None):
    if filters:
        filters_key_validator(filters)
    filters_validator(user, filters)
    filters = apply_scope(user, filters)
    res = get_users_with_data(filter_value=filters, con=con)
    event_alert = {'self': user['api_user_id'],"users": res, 'action': 'receive_user'}
    return event_alert


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
