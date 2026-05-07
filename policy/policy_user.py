"""
Validating input data from a business logic perspective
Checking object relationships for consistency with business logic
"""

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
        self.access = config['roles']['ROLES'][user.role]['permissions']['lead_user']

    def _access_user(self, action: str):
        if not self.access[action]:
            raise PermissionDenied(f" User {self.user.name} cannot access {action} users")

    def normalize_user_fields_by_role(self):
        roles = self.enum['ROLES']
        role_name = ""
        for i, k in roles.items():
            if k == self.cmd.role_id:
                role_name = i

        need_field = self.config['roles']['ROLES'][role_name]['required_field']
        if not need_field['branch_id']:
            self.cmd.branch_id = None
        if not need_field['depart_id']:
            self.cmd.depart_id = None
        for field, is_required in need_field.items():
            if is_required and not getattr(self.cmd, field):
                raise PermissionDenied(f" {role_name} requires {field}")
        return self.cmd

    def validate_cmd(self):
        if self.user.role == "MANAGER":
            if self.cmd.branch_id != self.user.branch_id:
                raise PermissionDenied("Manager can only change its branch")
            if self.cmd.role_id != self.enum['ROLES']['EMPLOYEE']:
                raise PermissionDenied("Manager can only actions EMPLOYEE")
            if self.cmd.depart_id is not None:
                raise PermissionDenied("Manager cannot assign depart_id")
        return self.cmd

    def check_modified(self, changed:User):
        if self.user.role == "MANAGER":
            if self.user.branch_id != changed.branch_id:
                raise PermissionDenied("Manager can not delete user from another branch")


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
    def role_filter(self):
        if self.user.role == "MANAGER":
            self.cmd.branch_id = self.user.branch_id
        return self.cmd
    def access_user(self):
        self._access_user("receive_user")