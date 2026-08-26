from core.enums import Role
from core.exceptions import CoreValidationBreak, PermissionDenied
from logger.logger import core_logger
from repository.unit_of_work import UoW
from core.ticket_core import User, Permission
from core.schemas import (CmdRenameUser, CmdCreateUser, CmdDeleteUser,
                          CmdChangeUser, QueryReceiveUser, CmdFirstUser)
class PolicyUser:
    """
    Base class for command policies.
    Handles config-based validation and user access control for specific functionality.
    """
    @staticmethod
    def normalize_cmd_by_role(cmd: CmdCreateUser|CmdChangeUser,
                              permission:dict):
        need_field = permission['required_field']
        if 'branch_id' not in need_field:
            cmd.branch_id = None
        if 'depart_id' not in need_field:
            cmd.depart_id = None
        return cmd

    @staticmethod
    def validate_cmd(cmd,
                     user: User):
        if user.role.name == Role.MANAGER.name:
            if cmd.branch_id:
                if cmd.branch_id != user.branch_id:
                    raise PermissionDenied("Manager can only change its branch")
            else:
                cmd.branch_id = user.branch_id
            if cmd.depart_id is not None:
                raise PermissionDenied("Manager cannot assign depart_id")
        return cmd

class UserService:
    def __init__(self, control: Permission, uow: UoW):
        self.uow = uow
        self.control = control

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
        return User(user_id=1,
                    user_name=cmd.user_name,
                     api_id=cmd.api_user_id,
                     role=Role.OWNER)

    def create(self,
                    actor: User,
                    cmd: CmdCreateUser
                    )->User:
        self.control.can(actor,'lead_user','create_user')
        check_user = self.uow.users.get({"api_user_id": cmd.api_user_id})
        PolicyUser.validate_cmd(cmd, actor)
        cmd = PolicyUser.normalize_cmd_by_role(cmd, self.control(cmd.role))
        if check_user:
            new_user = check_user[0]
            self.uow.users.activate(new_user.api_id)
        else:
            role_id = self.uow.role_mapper.get_roles_id(cmd.role.name)
            user_id = self.uow.users.create(
                        cmd.user_name,
                        cmd.api_user_id,
                        role_id,
                        depart_id=cmd.depart_id,
                        branch_id=cmd.branch_id)
            new_user = self.uow.users.get({'user_id': user_id})[0]
        return new_user

    def delete(self,
                    actor:User,
                    cmd: CmdDeleteUser)-> User:
        self.control.can(actor,'lead_user','delete_user')
        deletable = self.uow.users.get({"user_id": cmd.user_id})
        if not deletable:
            core_logger.error('User not found')
            raise CoreValidationBreak("User not found")
        deletable = deletable[0]
        self.uow.users.delete(cmd.user_id)
        return deletable

    def change(self,
                actor: User,
               cmd: CmdChangeUser)->User:
        changed = self.uow.users.get({'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        self.control.can(actor,'lead_user','change_user')
        cmd = PolicyUser.normalize_cmd_by_role(cmd,self.control(cmd.role))
        cmd = PolicyUser.validate_cmd(cmd,actor)
        role_id = self.uow.role_mapper.get_roles_id(cmd.role.name)
        self.uow.users.update(cmd.user_id,
                           role_id,
                           cmd.branch_id,
                           cmd.depart_id)
        modified = self.uow.users.get({'user_id': cmd.user_id})[0]
        return modified

    def rename(self,
            actor:User,
            cmd: CmdRenameUser)-> User:
        changed = self.uow.users.get({'user_id': cmd.user_id})
        if not changed:
            core_logger.error('User not found')
            raise CoreValidationBreak('User not found')
        self.control.can(actor,'lead_user','rename_user')
        self.uow.users.rename(cmd.user_id,cmd.user_name)
        modified =  self.uow.users.get({'user_id': cmd.user_id})[0]
        return modified

    def get(self,
             actor:User,
             cmd:QueryReceiveUser)->list[User]:
        self.control.can(actor,'lead_user','receive_user')
        cmd = PolicyUser.validate_cmd(cmd,actor)
        return self.uow.users.get(cmd.dict())

