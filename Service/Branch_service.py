from Service.Common import transactional,filters_key_validator,filters_validator,apply_scope
from Repository.write_model import branch_activate,branch_rename,branch_soft_del,branch_assert
from Repository.read_model import get_branch_with_data
from User_service import has_permission
from Logger.logger import core_logger
from Core.exceptions import ServiseValidationBreak,PermissionDenied
from Core.Ticket_core import User
from typing import Optional

@transactional
def lead_branches(user:Optional[User], action: str, config, name=None, branch_id=None, filters= None, con= None):
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
def receive_branch(user:Optional[User], filters=None, con=None):
    if filters:
        filters_key_validator(filters)
    filters_validator(user, filters)
    filters = apply_scope(user, filters)
    res = get_branch_with_data(filters, con=con)
    return res