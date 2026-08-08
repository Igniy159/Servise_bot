"""
The module is used to validate input data types through Pydantic and generate initial commands.
"""

from typing import Literal
from pydantic import BaseModel

from core.enums import Role, TypeTicket, State


class CmdCreateBranch(BaseModel):
    """Command for create branch"""
    name: str

class CmdRenameBranch(BaseModel):
    """Command for rename branch"""
    branch_id: int
    new_name: str


class QueryReceiveBranch(BaseModel):
    """Command for receive branch"""
    branch_activity: int | None = 1

class CmdDeleteBranch(BaseModel):
    """Command for delete branch"""
    branch_id: int


class CmdCreateTicket(BaseModel):
    """ Command for create ticket. Old name - EVENT DATA"""
    code_rule: int
    severity: TypeTicket
    comment: str
    file_id: str | None = None


class CmdCreateAlert(BaseModel):
    """Command for create alert"""
    code_alert: int
    comment: str

class CmdChangeState(BaseModel):
    """Command for reject ticket"""
    ticket_id: int
    new_state: State
    comment: str

class QueryGetAlerts(BaseModel):
    alert_id: int | None = None
    creator_id: int | None = None
    branch_id: int | None = None
    target_id: int | None = None

class QueryGetTicket(BaseModel):
    """ Command for get ticket with optional filter"""
    ticket_id: int | None = None
    branch_id: int | None = None
    depart_id: int | None = None
    creator_id: int | None = None
    state_id: int | None = None

class QueryGetHistoryTicket(BaseModel):
    """ Command for get history 1 ticket"""
    ticket_id: int

class CmdFirstUser(BaseModel):
    """Command for create first user"""
    user_name: str
    api_user_id: int

class CmdCreateUser(BaseModel):
    """Command for create user"""
    user_name: str
    api_user_id: int
    role: Role
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
    role: Role
    depart_id: int | None = None
    branch_id: int | None = None

class QueryReceiveUser(BaseModel):
    """ Command for get use with optional filter"""
    user_id: int | None = None
    api_user_id: int | None = None
    branch_id: int | None = None
    depart_id: int | None = None
    role_id: int | None = None
    user_activity: int | None = 1
