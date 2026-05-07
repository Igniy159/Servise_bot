"""
Branch service layer.
Contains use-case functions for branch management:
- create
- rename
- delete
- receive
Handles validation, filtering, and transaction boundaries.
"""
from sqlite3 import Connection
from core.exceptions import CoreValidationBreak
from api.command import CmdCreateBranch, CmdDeleteBranch, CmdRenameBranch, QueryReceiveBranch
from repository.write_model import branch_activate, branch_rename, branch_soft_del, branch_assert
from repository.read_model import get_branch_with_data
from core.ticket_core import User
from service.event_builder import EventBranch,EventGetBranch
from service.recipients import Recipient

def create_branch(user: User,
                  cmd: CmdCreateBranch,
                  con: Connection) -> tuple[EventBranch,Recipient]:
    """
    Creates or reactivates a branch in the database
    :param user: authenticated user performing the action
    :param cmd: name new branch
    :param con: active connect in db
    :return: event dict containing action result and metadata
    """
    with con:
        branch = get_branch_with_data(con,{"branch_name": cmd.name})
        if branch:
            branch = branch[0]
            branch_activate(branch['branch_id'], con)
        else:
            branch_assert(cmd.name, con)
            branch = get_branch_with_data(con,{"branch_name": cmd.name})
    event_alert = EventBranch(user,branch,'create_branch')
    recipient = Recipient(user)
    return event_alert, recipient



def rename_branch(user: User,
                  cmd: CmdRenameBranch,
                  con:Connection) -> tuple[EventBranch,Recipient]:
    """
    Overwrites the new name for the branch
    :param user: authenticated user performing the action
    :param cmd: ID for searching for a branch and changing it and new name
    :param con: active connect in db
    :return: event dict containing action result and metadata
    """
    with con:
        branch = get_branch_with_data(con,{"branch_id": cmd.branch_id})
        if not branch:
            raise CoreValidationBreak('Branch not found')
        branch_rename(cmd.branch_id, cmd.new_name, con=con)
        branch = get_branch_with_data(con,{"branch_id": cmd.branch_id})[0]
    event_alert = EventBranch(user, branch, 'rename_branch')
    recipient = Recipient(user)
    return event_alert, recipient


def receive_branch(user:User,
                   cmd:QueryReceiveBranch,
                   con:Connection)-> tuple[EventGetBranch,Recipient]:
    """
    shows user a list of branches
    :param user:  authenticated user performing the action
    :param cmd: filter from selection on db
    :param con: active connect in db
    :return: event containing a selection based on the branch filter
    """
    with con:
        branches = get_branch_with_data(con, dict(cmd))
    event_alert = EventGetBranch(user, branches)
    recipient = Recipient(user)
    return event_alert, recipient


def delete_branch(user: User,
                  cmd: CmdDeleteBranch,
                  con: Connection)-> tuple[EventBranch,Recipient]:
    """
    deactivates a branch without actually deleting it
    :param user: authenticated user performing the action
    :param cmd: deleted branch_id
    :param con: active connect in db
    :return: event dict containing action result and metadata
    """
    with con:
        branch = get_branch_with_data(con,{"branch_id": cmd.branch_id},)
        if not branch:
            raise CoreValidationBreak('Branch not found')
        branch_soft_del(cmd.branch_id, con)
    event_alert = EventBranch(user, branch[0], 'delete_branch')
    recipient = Recipient(user)
    return event_alert, recipient
