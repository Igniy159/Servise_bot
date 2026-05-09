"""
The module represents the boundary of the domain model.
Authorization occurs in this module.
Initial access checks to the service layer are also performed.
"""
from api.command import (
    CmdCreateBranch, CmdDeleteBranch, CmdRenameBranch, QueryReceiveBranch,
    CmdCreateTicket, CmdCloseTicket, CmdAssignTicket, CmdFinishTicket,
    CmdRejectTicket, CmdPriorityTicket, CmdConfirmTicket, CmdOnWaitingTicket,
    CmdOffWaitingTicket, QueryGetTicket, QueryGetHistoryTicket,
    CmdRenameUser, CmdCreateUser, CmdDeleteUser, CmdChangeUser, QueryReceiveUser, CmdFirstUser
)

from repository.unit_of_work import UoW
from service.branch_service import BranchService
from service.user_service import UserService
from service.ticket_service import TicketService
from core.exceptions import PermissionDenied
from core.ticket_core import User
from logger.logger import core_logger


class BaseController:
    """
    This class provides its descendants
    with user authorization
    and access control for the modules below.
    Rule all class output data -
    1. self.user - Actor
    2. cmd  - command action
    3. flag - flag action(optional)
    4. config - configuration from policy(optional)
    5. uow - configuration DB with connect
    """
    def __init__(self, config: dict, api_user_id: int, uow_factory: UoW) -> None:
        user = self._check_user(api_user_id)
        if user:
            self.user = User(user[0])
        else:
            raise PermissionDenied("User not found")
        self.config = config
        self.uow_factory = uow_factory
        self.user_access = self.config['roles']['ROLES'][self.user.role]['permissions']

    def _check_user(self, api_user: int):
        with self.uow_factory() as uow:
            user = uow.users.get({
        'user_activity': 1,
        'api_user_id': api_user
        })
            return user

    def _check_permission(self, flag: str) -> None:
        if not self.user_access.get(flag, False):
            core_logger.error(f"This changed {self.user.name} cannot use {flag} action")
            raise PermissionDenied(f'This {self.user.name} cannot use {flag} action')

class BranchController(BaseController):
    """
    This class calls service layer functions
     to manage the branch
    if the user has the "lead branch" access right.
    """

    def __init__(self, config: dict, api_user_id: int, uow: UoW) -> None:
        super().__init__(config, api_user_id, uow)
        self._check_permission('lead_branch')
        self.service = BranchService(uow)

    def create(self,cmd: CmdCreateBranch):
        """Calls the function to create a branch after authorization"""
        with self.uow_factory():
            return self.service.create(self.user,cmd)
    def rename(self,cmd:CmdRenameBranch):
        """Calls the function to rename a branch after authorization"""
        with self.uow_factory():
            return self.service.rename(self.user, cmd)
    def get(self,cmd:QueryReceiveBranch):
        """Calls the function to get branches with filters after authorization"""
        with self.uow_factory():
            return self.service.receive(self.user, cmd)
    def delete(self, cmd: CmdDeleteBranch):
        """Calls the function to delete a branch after authorization"""
        with self.uow_factory():
            return self.service.delete(self.user, cmd)


class TicketController(BaseController):
    """
    This class calls service layer functions
     to create or patch ticket
    if the user has the "lead ticket" access right.
    """

    def __init__(self, config:dict, api_user_id: int, uow:UoW):
        super().__init__(config, api_user_id,uow)
        self._check_permission('lead_ticket')
        self.service = TicketService(config, uow)


    def create(self,
               cmd: CmdCreateTicket):
        """
        The function causes a ticket to be created
         from the service layer with the command and user
        """
        return self.service.write(self.user,cmd)

    def update(self, cmd: CmdCloseTicket | CmdAssignTicket |CmdFinishTicket|
    CmdRejectTicket | CmdPriorityTicket| CmdConfirmTicket | CmdOnWaitingTicket |
    CmdOffWaitingTicket):
        """The function causes update ticket"""
        with self.uow_factory():
            return self.service.patch(self.user,cmd)


    def get(self,cmd:QueryGetTicket):
        """ The function sends a request
         to the service layer to receive tickets
          with a certain filtering/sorting"""
        with self.uow_factory():
            return self.service.get(self.user,cmd)


    def get_history(self,cmd:QueryGetHistoryTicket):
        """function sends a request
         to the service layer to receive history"""
        with self.uow_factory():
            return self.service.history(self.user,cmd)


class UserController(BaseController):
    """
    This class calls service layer functions
     to create or patch user
    if the user has the "lead users" access right.
    """

    def __init__(self, config:dict, api_user_id: int, uow):
        super().__init__(config, api_user_id, uow)
        self._check_permission('lead_user')
        self.service = UserService(config,uow)

    def create_first_user(self, cmd: CmdFirstUser):
        """The function create first user """
        with self.uow_factory():
            return self.service.create_first_owner(cmd)

    def create(self, cmd: CmdCreateUser):
        """The function create new user """
        with self.uow_factory():
            return self.service.create(self.user, cmd)

    def delete(self, cmd: CmdDeleteUser):
        """The function deletes user """
        with self.uow_factory():
            return self.service.delete(self.user,cmd)

    def change(self, cmd:CmdChangeUser):
        """The function causes a user to change here field.
        Need to clearly indicate the role and,
        preferably, other data (branch/department)"""
        with self.uow_factory():
            return self.service.change(self.user, cmd)

    def rename(self,cmd:CmdRenameUser):
        """The function renames the user"""
        with self.uow_factory():
            return self.service.rename(self.user, cmd)

    def get(self, cmd: QueryReceiveUser):
        """function sends a request
         to the service layer to receive users
         with optional filters"""
        with self.uow_factory():
            return self.service.get(self.user, cmd)
