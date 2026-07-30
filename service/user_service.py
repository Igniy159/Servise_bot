from policy.policy_user import PolicyUser
from core.exceptions import CoreValidationBreak
from logger.logger import core_logger
from repository.unit_of_work import UoW
from core.ticket_core import User
from api.command import (CmdRenameUser, CmdCreateUser, CmdDeleteUser,
                         CmdChangeUser, QueryReceiveUser, CmdFirstUser)

class UserService:
    def __init__(self, config:dict, uow: UoW):
        self.uow = uow
        permissions = config['roles']
        self.control = PolicyUser(permissions)

    def create_first_owner(self,
                           cmd: CmdFirstUser)-> User:
        """The function of initiating the very first user of the system,
         with the issuance of maximum access rights"""
        role_id = self.uow.role_mapper.get_roles_id("OWNER")
        existing_users = self.uow.users.get()
        if existing_users:
            raise CoreValidationBreak("System already initialized")
        self.uow.users.create(cmd.user_name,
                                     cmd.api_user_id,
                                     role_id=role_id)
        return User({'user_id':1,
                     'user_name': cmd.user_name,
                     'api_user_id':cmd.api_user_id,
                     'role_name': "OWNER"})

    def create(self,
                    actor: User,
                    cmd: CmdCreateUser
                    )->User:
        self.control.access_user(actor,'create_user')
        chek_user = self.uow.users.get({"api_user_id": cmd.api_user_id})
        if chek_user:
            new_user = chek_user[0]
            self.uow.users.activate(new_user['api_user_id'])
        else:
            self.control.validate_cmd(cmd,actor)
            cmd = self.control.normalize_cmd_by_role(actor,cmd)
            role_id =  self.uow.role_mapper.get_roles_id(cmd.role.name)
            user_id = self.uow.users.create(
                        cmd.user_name,
                        cmd.api_user_id,
                        role_id,
                        depart_id=cmd.depart_id,
                        branch_id=cmd.branch_id)
            new_user = cmd.dict()
            new_user['user_id'] = user_id
        return User(new_user)

    def delete(self,
                    actor:User,
                    cmd: CmdDeleteUser)-> User:
        self.control.access_user(actor,'delete_user')
        deletable = self.uow.users.get({"user_id": cmd.user_id})
        if not deletable:
            core_logger.error('User not found')
            raise CoreValidationBreak("User not found")
        deletable = User(deletable[0])
        self.uow.users.delete(cmd.user_id)
        return deletable

    def change(self,
                actor: User,
               cmd: CmdChangeUser)->User:
        changed = self.uow.users.get({'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        self.control.access_user(actor,'change_user')
        cmd = self.control.normalize_cmd_by_role(actor,cmd)
        cmd = self.control.validate_cmd(cmd,actor)
        role_id = self.uow.role_mapper.get_roles_id(cmd.role.name)
        self.uow.users.update(cmd.user_id,
                           role_id,
                           cmd.branch_id,
                           cmd.depart_id)
        modified = User(self.uow.users.get({'user_id': cmd.user_id})[0])
        return modified

    def rename(self,
            actor:User,
            cmd: CmdRenameUser)-> User:
        changed = self.uow.users.get({'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        self.control.access_user(actor,'rename_user')
        self.uow.users.rename(cmd.user_id,cmd.user_name)
        modified = User(self.uow.users.get({'user_id': cmd.user_id})[0])
        return modified

    def get(self,
             actor:User,
             cmd:QueryReceiveUser)->list[User]:
        self.control.access_user(actor,'receive_user')
        cmd = self.control.validate_cmd(cmd,actor)
        users = self.uow.users.get(cmd.dict())
        return [User(user) for user in users]
