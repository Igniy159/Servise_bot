"""
The module represents the boundary of the domain model.
Authorization occurs in this module.
Initial access checks to the service layer are also performed.
"""
from typing import Optional
from api.command import CmdFirstUser
from core.exceptions import PermissionDenied
from repository.unit_of_work import UoW
from service.alert_service import AlertService
from service.branch_service import BranchService
from service.user_service import UserService
from service.ticket_service import TicketService
from core.ticket_core import User

class AuthController:
    def __init__(self,
                 user_name: str,
                 api_user_id: int,
                 first_owner_id: int,
                 uow: UoW,
                 user_service: UserService
                 ):
        self.user_name = user_name
        self.api_user_id = api_user_id
        self.first_owner_id = first_owner_id
        self.uow = uow
        self.user_service = user_service

    def auth(self)-> Optional[User]:
        users = self.uow.users.get(filter_value={'api_user_id': self.api_user_id})
        user = users[0] if users else None
        if user:
            return user
        if self.api_user_id == self.first_owner_id and not users:
            command = CmdFirstUser(user_name=self.user_name,api_user_id=self.api_user_id)
            return self.user_service.create_first_owner(command)
        raise PermissionDenied('401 Unauthorized')

class ServiceFactory:
    def __init__(self,
                 raw_config:dict,
                 uow: UoW):
        self.ticket_service = TicketService(raw_config,uow)
        self.user_service = UserService(raw_config,uow)
        self.branch_service = BranchService(raw_config,uow)
        self.alert_service = AlertService(raw_config, uow)
