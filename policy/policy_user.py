"""
Validating input data from a business logic perspective
Checking object relationships for consistency with business logic
"""
from core.enums import Role
from core.ticket_core import User
from core.exceptions import PermissionDenied
class PolicyUser:
    """
    Base class for command policies.
    Handles config-based validation and user access control for specific functionality.
    """
    def __init__(self, user: User, config:dict, cmd):
        self.user = user
        self.cmd = cmd
        self.config = config
        self.enum = config['enum']
        self.access = config['roles'][user.role.name]['permissions']['lead_user']

    def _access_user(self, action: str):
        if not self.access[action]:
            raise PermissionDenied(f"User {self.user.name} cannot access {action} users")

    def normalize_cmd_by_role(self):
        need_field = self.config['roles'][self.cmd.role.name]['required_field']
        if 'branch_id' not in need_field:
            self.cmd.branch_id = None
        if 'depart_id' not in need_field:
            self.cmd.depart_id = None
        return self.cmd

    def validate_cmd(self):
        if self.user.role == Role.MANAGER:
            if self.cmd.branch_id != self.user.branch_id:
                raise PermissionDenied("Manager can only change its branch")
            if self.cmd.role.name != self.enum['ROLES']['EMPLOYEE']:
                raise PermissionDenied("Manager can only actions EMPLOYEE")
            if self.cmd.depart_id is not None:
                raise PermissionDenied("Manager cannot assign depart_id")
            self.cmd.branch_id = self.user.branch_id
        return self.cmd

class PolicyCreateUser(PolicyUser):
    def access_user(self):
        self._access_user("create_user")
class PolicyDeleteUser(PolicyUser):
    def access_user(self):
        self._access_user("delete_user")
class PolicyChangeUser(PolicyUser):
    def access_user(self):
        self._access_user("change_user")
class PolicyRenameUser(PolicyUser):
    def access_user(self):
        self._access_user("rename_user")
class PolicyGetUsers(PolicyUser):
    def access_user(self):
        self._access_user("receive_user")
