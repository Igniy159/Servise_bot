"""
Branch service layer.
Contains use-case functions for branch management:
- create
- rename
- delete
- receive
Handles validation, filtering, and transaction boundaries.
"""
from core.exceptions import CoreValidationBreak
from core.ticket_core import User
from api.command import CmdCreateBranch, CmdDeleteBranch, CmdRenameBranch, QueryReceiveBranch
from repository.unit_of_work import UoW
from service.event_builder import EventBranch,EventGetBranch
from service.recipients import Recipient

class BranchService:
    def __init__(self, uow: UoW):
        self.uow = uow

    def create(self,
              user: User,
              cmd: CmdCreateBranch) -> tuple[EventBranch,Recipient]:
        """
        Creates or reactivates a branch in the database
        :param user: authenticated user performing the action
        :param cmd: name new branch
        :return: event dict containing action result and metadata
        """
        branch = self.uow.branches.get({"branch_name": cmd.name})
        if branch:
            branch = branch[0]
            self.uow.branches.activate(branch['branch_id'])
        else:
            self.uow.branches.create(cmd.name)
            branch =  self.uow.branches.get({"branch_name": cmd.name})
        event_alert = EventBranch(user,branch,'create_branch')
        recipient = Recipient(user)
        return event_alert, recipient

    def rename(self,
               user: User,
               cmd: CmdRenameBranch) -> tuple[EventBranch,Recipient]:
        """
        Overwrites the new name for the branch
        :param user: authenticated user performing the action
        :param cmd: ID for searching for a branch and changing it and new name
        :return: event dict containing action result and metadata
        """
        branch = self.uow.branches.get({"branch_id": cmd.branch_id})
        if not branch:
            raise CoreValidationBreak('Branch not found')
        self.uow.branches.rename(cmd.branch_id, cmd.new_name)
        branch = self.uow.branches.get({"branch_id": cmd.branch_id})[0]
        event_alert = EventBranch(user, branch, 'rename_branch')
        recipient = Recipient(user)
        return event_alert, recipient


    def receive(self,
               user:User,
               cmd:QueryReceiveBranch
                )-> tuple[EventGetBranch,Recipient]:
        """
        shows user a list of branches
        :param user:  authenticated user performing the action
        :param cmd: filter from selection on db
        :return: event containing a selection based on the branch filter
        """
        branches = self.uow.branches.get(dict(cmd))
        event_alert = EventGetBranch(user, branches)
        recipient = Recipient(user)
        return event_alert, recipient


    def delete(self,
              user: User,
              cmd: CmdDeleteBranch)-> tuple[EventBranch,Recipient]:
        """
        deactivates a branch without actually deleting it
        :param user: authenticated user performing the action
        :param cmd: deleted branch_id
        :return: event dict containing action result and metadata
        """
        branch = self.uow.branches.get({"branch_id": cmd.branch_id},)
        if not branch:
            raise CoreValidationBreak('Branch not found')
        self.uow.branches.delete(cmd.branch_id)
        event_alert = EventBranch(user, branch[0], 'delete_branch')
        recipient = Recipient(user)
        return event_alert, recipient
