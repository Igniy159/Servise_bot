from policy.policy_user import (PolicyCreateUser, PolicyDeleteUser,
                                PolicyChangeUser, PolicyRenameUser, PolicyGetUsers)
from core.exceptions import CoreValidationBreak
from logger.logger import core_logger
from repository.unit_of_work import UoW
from core.ticket_core import User
from api.command import (CmdRenameUser, CmdCreateUser, CmdDeleteUser,
                         CmdChangeUser, QueryReceiveUser, CmdFirstUser)
from service.event_builder import EventUser, EventGetUser
from service.recipients import RecipientUser, Recipient

class UserService:
    def __init__(self, config:dict, uow: UoW):
        self.uow = uow
        self.config = config

    def create_first_owner(self,
                           cmd: CmdFirstUser):
        """The function of initiating the very first user of the system,
         with the issuance of maximum access rights"""
        role = self.config['enum']['ROLES']['OWNER']
        existing_owner = self.uow.users.get({'role_id': role})
        if existing_owner:
            raise CoreValidationBreak("Owner already exists")
        return self.uow.users.create(cmd.user_name,cmd.api_user_id,role_id=role)

    def create(self,
                    actor: User,
                    cmd: CmdCreateUser
                    )->tuple[EventUser,RecipientUser]:

        control = PolicyCreateUser(actor,self.config,cmd)
        control.access_user()
        chek_user = self.uow.users.get({"api_user_id": cmd.api_user_id})
        if chek_user:
            new_user = chek_user[0]
            self.uow.users.activate(new_user['api_user_id'])
        else:
            control.validate_cmd()
            cmd = control.normalize_user_fields_by_role()
            user_id = self.uow.users.create(
                        cmd.name,
                        cmd.api_user_id,
                        cmd.role_id,
                        depart_id=cmd.depart_id,
                        branch_id=cmd.branch_id
                        )
            new_user = dict(cmd)
            new_user['user_id'] = user_id
        event_alert = EventUser(actor,User(new_user),"create_user")
        recipient = RecipientUser(actor,User(new_user))
        return event_alert, recipient

    def delete(self,
                    actor:User,
                    cmd: CmdDeleteUser)->tuple[EventUser,RecipientUser]:
        control = PolicyDeleteUser(actor,self.config,cmd)
        control.access_user()
        deletable = self.uow.users.get({"user_id": cmd.user_id})
        if not deletable:
            core_logger.error('User not found')
            raise CoreValidationBreak("User not found")
        deletable = User(deletable[0])
        control.check_modified(deletable)
        self.uow.users.delete(cmd.user_id)
        event_alert = EventUser(actor,deletable,"delete_user")
        recipient = RecipientUser(actor,deletable)
        return event_alert, recipient

    def change(self,
                actor: User,
               cmd: CmdChangeUser)->tuple[EventUser,RecipientUser]:
        changed = self.uow.users.get({'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        control = PolicyChangeUser(actor,self.config,cmd)
        control.access_user()
        control.check_modified(User(changed[0]))
        cmd = control.normalize_user_fields_by_role()
        control.validate_cmd()
        self.uow.users.update(cmd.user_id,
                           cmd.role_id,
                           cmd.branch_id,
                           cmd.depart_id)
        modified = User(self.uow.users.get({'user_id': cmd.user_id})[0])
        event_alert = EventUser(actor,modified,"change_user")
        recipient = RecipientUser(actor,modified)
        return event_alert, recipient

    def rename(self,
            actor:User,
            cmd: CmdRenameUser)->tuple[EventUser,RecipientUser]:
        changed = self.uow.users.get({'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        changed = User(changed[0])
        control = PolicyRenameUser(actor,self.config,cmd)
        control.access_user()
        control.check_modified(changed)
        self.uow.users.rename(cmd.user_id,cmd.user_name)
        modified = User(self.uow.users.get({'user_id': cmd.user_id})[0])
        event_alert = EventUser(actor,modified,"rename_user")
        recipient = RecipientUser(actor,changed)
        return event_alert, recipient

    def get(self,
             actor:User,
             cmd:QueryReceiveUser)->tuple[EventGetUser,Recipient]:
        control = PolicyGetUsers(actor,self.config,cmd)
        control.access_user()
        cmd = control.role_filter()
        users = self.uow.users.get(cmd)
        event_alert = EventGetUser(actor,users)
        recipient = Recipient(actor)
        return event_alert, recipient
