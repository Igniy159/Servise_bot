from core.exceptions import PermissionDenied
from core.ticket_core import User


class PolicyBranch:
    def __init__(self, permissions:dict):
        self.permissions = permissions

    def access_user(self,
                    actor:User,
                    action: str):
        access = self.permissions[actor.role.name]['permissions']['lead_branch']
        if not access[action]:
            raise PermissionDenied(f"User {actor.name} cannot access {action} users")
