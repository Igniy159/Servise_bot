"""
The module represents the boundary of the domain model.
Authorization occurs in this module.
Initial access checks to the service layer are also performed.
"""
from api.command import (
CmdCreateBranch, CmdDeleteBranch, CmdRenameBranch, QueryReceiveBranch,
CmdCreateTicket, CmdCloseTicket, CmdAssignTicket, CmdFinishTicket,
CmdRejectTicket,CmdPriorityTicket,CmdConfirmTicket, CmdOnWaitingTicket,
CmdOffWaitingTicket, QueryGetTicket, QueryGetHistoryTicket,
CmdRenameUser, CmdCreateUser, CmdDeleteUser, CmdChangeUser, QueryReceiveUser
)
from service.branch_service import create_branch, rename_branch, receive_branch, delete_branch
from service.user_service import delete_user,change_user,create_user,receive_user,rename_user
from service.common import check_user
from service.ticket_service import CreatorTicket, UpdaterTicket, receive_history, GetterTicket
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
    5. con - connection from DB
    """
    def __init__(self, config: dict, api_user_id: int, con=None) -> None:
        user = check_user(api_user_id, con=con)
        if user:
            self.user = User(user[0])
        else:
            raise PermissionDenied("User not found")
        self.config = config
        self.con = con
        self.user_access = self.config['roles'][self.user.role]['permissions']

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
    def __init__(self, config, api_user_id: int):
        super().__init__(config, api_user_id)
        self._check_permission('lead_branch')

    def create_branch(self,cmd: CmdCreateBranch):
        """Calls the function to create a branch after authorization"""
        return create_branch(self.user,cmd,con=self.con)
    def rename_branch(self,cmd:CmdRenameBranch):
        """Calls the function to rename a branch after authorization"""
        return rename_branch(self.user, cmd,con=self.con)
    def receive_branch(self,cmd:QueryReceiveBranch):
        """Calls the function to get branches with filters after authorization"""
        return receive_branch(self.user, cmd, con=self.con)
    def delete_branch(self, cmd: CmdDeleteBranch):
        """Calls the function to delete a branch after authorization"""
        return delete_branch(self.user, cmd, con=self.con)


class TicketController(BaseController):
    """
    This class calls service layer functions
     to create or patch ticket
    if the user has the "lead ticket" access right.
    """

    def __init__(self, config, api_user_id: int):
        super().__init__(config, api_user_id)
        self._check_permission('lead_ticket')

    def create(self,
               cmd: CmdCreateTicket):
        """
        The function causes a ticket to be created
         from the service layer with the command and user
        """
        return CreatorTicket(self.user, cmd, self.config, self.con).write_ticket()

    def confirm(self, cmd: CmdConfirmTicket):
        """The function causes a ticket to be confirmed"""
        return UpdaterTicket(self.user, cmd,self.config, self.con).apply_write_patch()

    def reject(self, cmd: CmdRejectTicket):
        """The function causes a ticket to be rejected"""
        return UpdaterTicket(self.user, cmd,self.config, self.con).apply_write_patch()

    def priority(self, cmd: CmdPriorityTicket):
        """The function causes a ticket to be changed priority"""
        return UpdaterTicket(self.user, cmd,self.config, self.con).apply_write_patch()

    def assign(self, cmd:CmdAssignTicket):
        """The function causes a ticket to be assigned to"""
        return UpdaterTicket(self.user, cmd, self.config, self.con).apply_write_patch()

    def on_waiting(self, cmd:CmdOnWaitingTicket):
        """The function causes a ticket to be on_waiting """
        return UpdaterTicket(self.user, cmd, self.config,self.con).apply_write_patch()

    def off_waiting(self, cmd: CmdOffWaitingTicket):
        """The function causes a ticket to be off waiting """
        return UpdaterTicket(self.user, cmd, self.config, self.con).apply_write_patch()

    def finish(self, cmd: CmdFinishTicket):
        """The function causes a ticket to be finish """
        return UpdaterTicket(self.user, cmd, self.config, self.con).apply_write_patch()

    def close(self,cmd: CmdCloseTicket):
        """The function causes a ticket to be closed """
        return UpdaterTicket( self.user, cmd, self.config, self.con).apply_write_patch()

    def get_ticket(self,cmd:QueryGetTicket):
        """ The function sends a request
         to the service layer to receive tickets
          with a certain filtering/sorting"""
        return GetterTicket(self.user,cmd,self.config,con=self.con).receive_tickets()


    def get_history_ticket(self,cmd:QueryGetHistoryTicket):
        """function sends a request
         to the service layer to receive history"""
        return receive_history(self.user, cmd, self.config, con=self.con)



class UserController(BaseController):
    """
    This class calls service layer functions
     to create or patch user
    if the user has the "lead users" access right.
    """

    def __init__(self, config, api_user_id: int):
        super().__init__(config, api_user_id)
        self._check_permission('lead_user')

    def create_user(self, cmd: CmdCreateUser):
        """The function create new user """
        return create_user(self.user, cmd, self.config, con=self.con)

    def delete_user(self, cmd: CmdDeleteUser):
        """The function deletes user """
        return delete_user(self.user,cmd ,con=self.con)


    def change_user(self, cmd:CmdChangeUser):
        """The function causes a user to change here field.
        Need to clearly indicate the role and,
        preferably, other data (branch/department)"""
        return change_user(self.user, cmd, con=self.con)

    def rename_user(self,cmd:CmdRenameUser):
        """The function renames the user"""
        return rename_user(self.user, cmd, con=self.con)

    def receive_users(self,cmd: QueryReceiveUser)-> list[dict]:
        """function sends a request
         to the service layer to receive users
         with optional filters"""
        return receive_user(self.user, cmd, con=self.con)
