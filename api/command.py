"""
The module is used to validate input data types through Pydantic and generate initial commands.
"""

from typing import Literal
from pydantic import BaseModel

class CmdCreateBranch(BaseModel):
    """Command for create branch"""
    name: str

class CmdRenameBranch(BaseModel):
    """Command for rename branch"""
    branch_id: int
    new_name: str


class QueryReceiveBranch(BaseModel):
    """Command for receive branch"""
    branch_id: int | None = None
    branch_name: str | None = None
    branch_activity: int | None = 1


class CmdDeleteBranch(BaseModel):
    """Command for delete branch"""
    branch_id: int


class CmdCreateTicket(BaseModel):
    """ Command for create ticket. Old name - EVENT DATA"""
    problem_category: str
    problem_name: str
    problem_class: str
    problem_type: str | None = None
    zone: str | None = None
    comment: str | None = None
    priority: str | None = None
    branch_id: int | None = None


class CmdRejectTicket(BaseModel):
    """Command for reject ticket"""
    ticket_id: int
    reject_comment: str


class CmdPriorityTicket(BaseModel):
    """ Command for change priority ticket"""
    ticket_id: int
    new_priority_id: int
    comment: str | None = None


class CmdConfirmTicket(BaseModel):
    """Command for actions confirm """
    ticket_id: int
    comment: str | None = None

class CmdAssignTicket(BaseModel):
    """Command for actions assign ticket"""
    ticket_id: int
    comment: str | None = None

class CmdOnWaitingTicket(BaseModel):
    """Command for actions ON waiting """
    ticket_id: int
    comment: str | None = None

class CmdOffWaitingTicket(BaseModel):
    """Command for actions Off waiting ticket"""
    ticket_id: int
    comment: str | None = None

class CmdFinishTicket(BaseModel):
    """Command for actions finish ticket"""
    ticket_id: int
    comment: str | None = None

class CmdCloseTicket(BaseModel):
    """Command for actions close ticket"""
    ticket_id: int
    comment: str | None = None

class QueryGetTicket(BaseModel):
    """ Command for get ticket with optional filter"""
    ticket_id: int | None = None
    zone: str | None = None
    branch_id: int | None = None
    depart_id: int | None = None
    creator_id: int | None = None
    status: int | None = None
    priority: int | None = None
    sort_priority: Literal['asc','desc'] = 'asc'
    sort_status: Literal['asc','desc']  = 'asc'
    size: Literal['full','short'] = 'short'

class QueryGetHistoryTicket(BaseModel):
    """ Command for get history 1 ticket"""
    ticket_id: int

class CmdFirstUser(BaseModel):
    user_name: str
    api_user_id: int

class CmdCreateUser(BaseModel):
    """Command for create user"""
    user_name: str
    api_user_id: int
    role_id: int
    depart_id: int | None = None
    branch_id: int | None = None

class CmdDeleteUser(BaseModel):
    """Command for delete user"""
    user_id: int

class CmdRenameUser(BaseModel):
    """Command for rename user"""
    user_id: int
    user_name: str

class CmdChangeUser(BaseModel):
    """
    Command for change user.
    For business reasons, it is advisable to provide complete data
    """
    user_id: int
    user_role_id: int
    user_depart_id: int | None = None
    user_branch_id: int | None = None

class QueryReceiveUser(BaseModel):
    """ Command for get use with optional filter"""
    user_id: int | None = None
    api_user_id: int | None = None
    user_branch_id: int | None = None
    user_depart_id: int | None = None
    user_role_id: int | None = None
    user_activity: int | None = 1
