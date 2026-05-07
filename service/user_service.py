from sqlite3 import Connection

from policy.policy_user import PolicyCreateUser, PolicyDeleteUser, PolicyChangeUser, PolicyRenameUser, PolicyGetUsers
from core.exceptions import CoreValidationBreak
from logger.logger import core_logger
from repository.write_model import user_assert,user_activate,user_soft_del,update_user_params,update_user_name
from repository.read_model import get_users_with_data
from core.ticket_core import User
from api.command import CmdRenameUser, CmdCreateUser, CmdDeleteUser, CmdChangeUser, QueryReceiveUser, CmdFirstUser
from service.event_builder import EventUser, EventGetUser
from service.recipients import RecipientUser, Recipient



def create_first_owner(cmd: CmdFirstUser,config,con):
    """The function of initiating the very first user of the system,
     with the issuance of maximum access rights"""
    role = config['enum']['ROLES']['OWNER']
    with con:
        existing_owner = get_users_with_data(
            filter_value={'role_id': role},
            con=con)
        if existing_owner:
            raise CoreValidationBreak("Owner already exists")
        return user_assert(con,cmd.user_name,cmd.api_user_id,role_id=role)


def create_user(actor: User,
                cmd: CmdCreateUser,
                config: dict,
                con: Connection)->tuple[EventUser,RecipientUser]:

    control = PolicyCreateUser(actor,config,cmd)
    control.access_user()
    with con:
        chek_user = get_users_with_data(filter_value={"api_user_id": cmd.api_user_id}, con=con)
        if chek_user:
            user_activate(chek_user[0]['api_user_id'], con=con)
            new_user = chek_user[0]
        else:
            control.validate_cmd()
            cmd = control.normalize_user_fields_by_role()
            user_id = user_assert(con,
                        cmd.name,
                        cmd.api_user_id,
                        cmd.role_id,
                        depart_id=cmd.depart_id,
                        branch_id=cmd.branch_id,
                        )
            new_user = dict(cmd)
            new_user['user_id'] = user_id
    event_alert = EventUser(actor,User(new_user),"create_user")
    recipient = RecipientUser(actor,User(new_user))
    return event_alert, recipient


def delete_user(actor:User,
                cmd: CmdDeleteUser,
                config:dict,
                con: Connection)->tuple[EventUser,RecipientUser]:
    control = PolicyDeleteUser(actor,config,cmd)
    control.access_user()
    with con:
        deletable = get_users_with_data(con,{"user_id": cmd.user_id})
        if not deletable:
            core_logger.error('User not found')
            raise CoreValidationBreak("User not found")
        deletable = User(deletable[0])
        control.check_modified(deletable)
        user_soft_del(cmd.user_id,con)
    event_alert = EventUser(actor,deletable,"delete_user")
    recipient = RecipientUser(actor,deletable)
    return event_alert, recipient


def change_user(actor: User,
               cmd: CmdChangeUser,
                config:dict,
               con:Connection)->tuple[EventUser,RecipientUser]:
    with con:
        changed = get_users_with_data(con,{'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        control = PolicyChangeUser(actor,config,cmd)
        control.access_user()
        control.check_modified(User(changed[0]))
        cmd = control.normalize_user_fields_by_role()
        control.validate_cmd()
        update_user_params(cmd.user_id,
                           cmd.role_id,
                           cmd.branch_id,
                           cmd.depart_id,
                           con)
        modified = User(get_users_with_data(con,{'user_id': cmd.user_id})[0])
    event_alert = EventUser(actor,modified,"change_user")
    recipient = RecipientUser(actor,modified)
    return event_alert, recipient


def rename_user(actor:User,
                cmd: CmdRenameUser,
                config:dict,
                con:Connection)->tuple[EventUser,RecipientUser]:
    with con:
        changed = get_users_with_data(con,{'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        changed = User(changed[0])
        control = PolicyRenameUser(actor,config,cmd)
        control.access_user()
        control.check_modified(changed)
        update_user_name(cmd.user_id,cmd.user_name,con)
        modified = User(get_users_with_data(con,{'user_id': cmd.user_id})[0])
    event_alert = EventUser(actor,modified,"rename_user")
    recipient = RecipientUser(actor,changed)
    return event_alert, recipient



def receive_user(actor:User,
                 cmd:QueryReceiveUser,
                config:dict,
                 con:Connection)->tuple[EventGetUser,Recipient]:
    control = PolicyGetUsers(actor,config,cmd)
    control.access_user()
    cmd = control.role_filter()
    with con:
        users = get_users_with_data(con, cmd)
    event_alert = EventGetUser(actor,users)
    recipient = Recipient(actor)
    return event_alert, recipient
