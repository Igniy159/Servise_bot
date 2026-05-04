"""
Branch service layer.
Contains use-case functions for branch management:
- create
- rename
- delete
- receive
Handles validation, filtering, and transaction boundaries.
"""
from typing import Optional
from service.common import transactional, filters_key_validator, filters_validator, apply_scope
from api.command import CmdCreateBranch, CmdDeleteBranch, CmdRenameBranch, QueryReceiveBranch
from repository.write_model import branch_activate, branch_rename, branch_soft_del, branch_assert
from repository.read_model import get_branch_with_data
from logger.logger import core_logger
from core.exceptions import ServiseValidationBreak
from core.ticket_core import User


@transactional
def create_branch(user: User, cmd: CmdCreateBranch, con=None) -> dict:
    """
    Creates or reactivates a branch in the database
    :param user: authenticated user performing the action
    :param cmd: name new branch
    :param con: active connect in db
    :return: event dict containing action result and metadata
    """
    if not name or not name.strip():
        core_logger.error("Name cannot be empty")
        raise ServiseValidationBreak("Name cannot be empty")
    branch = get_branch_with_data(filter_value={"branch_name": name}, con=con)
    if branch:
        branch = branch[0]
        branch_activate(branch['branch_id'], con=con)
    else:
        branch_assert(name, con=con)
    event_alert = {'branch_name': name, 'action': 'create_branch', 'self': user.api_id}
    return event_alert


@transactional
def rename_branch(user: User, cmd: CmdRenameBranch, con=None):
    """
    Overwrites the new name for the branch
    :param user: authenticated user performing the action
    :param cmd: ID for searching for a branch and changing it and new name
    :param con: active connect in db
    :return: event dict containing action result and metadata
    """
    if not name or not name.strip():
        core_logger.error("Name cannot be empty")
        raise ServiseValidationBreak("Name cannot be empty")
    branch_rename(branch_id, name, con=con)
    event_alert = {'branch_name': name, 'action': 'rename_branch', 'self': user.api_id}
    return event_alert


@transactional
def receive_branch(user: User, cmd:QueryReceiveBranch, con=None):
    """
    shows user a list of branches
    :param user:  authenticated user performing the action
    :param cmd: filter from selection on db
    :param con: active connect in db
    :return: event containing a selection based on the branch filter
    """
    if filters:
        filters_key_validator(filters)
    filters_validator(user, filters)
    filters = apply_scope(user, filters)
    branches = get_branch_with_data(filters, con=con)
    event_alert = {'action': 'receive_branch', 'branches': branches, 'self': user.api_id}
    return event_alert


@transactional
def delete_branch(user: User, cmd: CmdDeleteBranch, con=None):
    """
    deactivates a branch without actually deleting it
    :param user: authenticated user performing the action
    :param cmd: deleted branch_id
    :param con: active connect in db
    :return: event dict containing action result and metadata
    """
    branch_soft_del(branch_id, con=con)
    event_alert = {'action': 'delete_branch',
                   'branch_id': branch_id,
                   'self': user.api_id}
    return event_alert
