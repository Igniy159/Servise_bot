"""
Validating input data from a business logic perspective
Checking object relationships for consistency with business logic
"""
from api.command import CmdCreateUser, CmdChangeUser
from core.enums import Role
from core.ticket_core import User
from core.exceptions import PermissionDenied
class PolicyUser:
    """
    Base class for command policies.
    Handles config-based validation and user access control for specific functionality.
    """
    def __init__(self, permissions:dict):
        self.permissions = permissions

    def access_user(self,
                    user: User,
                    action: str):
        access = self.permissions[user.role.name]['permissions']['lead_user']
        if not access[action]:
            raise PermissionDenied(f"User {user.name} cannot access {action} users")

    def normalize_cmd_by_role(self,
                              user: User,
                              cmd: CmdCreateUser|CmdChangeUser):
        need_field = self.permissions[user.role.name]['required_field']
        if 'branch_id' not in need_field:
            cmd.branch_id = None
        if 'depart_id' not in need_field:
            cmd.depart_id = None
        return cmd

    @staticmethod
    def validate_cmd(cmd,
                     user: User
                     ):
        if user.role.name == Role.MANAGER.name:
            if cmd.branch_id:
                if cmd.branch_id != user.branch_id:
                    raise PermissionDenied("Manager can only change its branch")
            else:
                cmd.branch_id = user.branch_id
            if cmd.depart_id is not None:
                raise PermissionDenied("Manager cannot assign depart_id")
        return cmd
