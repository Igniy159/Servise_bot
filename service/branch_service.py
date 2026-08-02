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
from core.ticket_core import User, Branch
from api.command import CmdCreateBranch, CmdDeleteBranch, CmdRenameBranch, QueryReceiveBranch
from policy.policy_branch import PolicyBranch
from repository.unit_of_work import UoW

class BranchService:
    def __init__(self,
                 raw_config:dict,
                 uow: UoW):
        self.uow = uow
        self.control = PolicyBranch(raw_config['roles'])


    def create(self,
               actor:User,
               cmd: CmdCreateBranch
               )->Branch:
        self.control.access_user(actor,'create_branch')
        branch = self.uow.branches.get({"branch_name": cmd.name})
        if branch:
            branch = branch[0]
            self.uow.branches.activate(branch.id)
        else:
            self.uow.branches.create(cmd.name)
            branch = self.uow.branches.get({"branch_name": cmd.name})[0]
        return branch

    def rename(self,
               actor:User,
               cmd: CmdRenameBranch
               ) -> Branch:
        self.control.access_user(actor,'rename_branch')
        branch = self.uow.branches.get({"branch_id": cmd.branch_id})
        if not branch:
            raise CoreValidationBreak('Branch not found')
        self.uow.branches.rename(cmd.branch_id, cmd.new_name)
        return self.uow.branches.get({"branch_id": cmd.branch_id})[0]


    def receive(self,
                actor: User,
                cmd:QueryReceiveBranch
                )-> list[Branch]:
        self.control.access_user(actor, 'receive_branch')
        return self.uow.branches.get(dict(cmd))


    def delete(self,
               actor: User,
               cmd: CmdDeleteBranch)-> Branch:
        self.control.access_user(actor,'delete_branch')
        branch = self.uow.branches.get({"branch_id": cmd.branch_id},)
        if not branch:
            raise CoreValidationBreak('Branch not found')
        self.uow.branches.delete(cmd.branch_id)
        return branch[0]
