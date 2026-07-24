"""
Branch service layer.
Contains use-case functions for branch management:
- create
- rename
- delete
- receive
Handles validation, filtering, and transaction boundaries.
"""
from core.exceptions import CoreValidationBreak, PermissionDenied
from core.ticket_core import User, Branch
from api.command import CmdCreateBranch, CmdDeleteBranch, CmdRenameBranch, QueryReceiveBranch
from repository.unit_of_work import UoW

class BranchService:
    def __init__(self, uow: UoW, user: User, accesses:dict):
        self.uow = uow
        self.user = user
        self.access = accesses
        self._check_access()

    def _check_access(self):
        if not self.access[self.user.role]['permissions']['lead_branch']:
            raise PermissionDenied('User not access')

    def create(self, cmd: CmdCreateBranch)->Branch:
        branch = self.uow.branches.get({"branch_name": cmd.name})
        if branch:
            branch = branch[0]
            self.uow.branches.activate(branch['branch_id'])
        else:
            self.uow.branches.create(cmd.name)
            branch = self.uow.branches.get({"branch_name": cmd.name})
            print(branch[0])
        return Branch(branch[0])

    def rename(self, cmd: CmdRenameBranch) -> Branch:
        branch = self.uow.branches.get({"branch_id": cmd.branch_id})
        if not branch:
            raise CoreValidationBreak('Branch not found')
        self.uow.branches.rename(cmd.branch_id, cmd.new_name)
        return Branch(self.uow.branches.get({"branch_id": cmd.branch_id})[0])


    def receive(self,cmd:QueryReceiveBranch)-> list[Branch]:
        branches = self.uow.branches.get(dict(cmd))
        return [Branch(i) for i in branches]


    def delete(self, cmd: CmdDeleteBranch)-> Branch:
        branch = self.uow.branches.get({"branch_id": cmd.branch_id},)
        if not branch:
            raise CoreValidationBreak('Branch not found')
        self.uow.branches.delete(cmd.branch_id)
        return Branch(branch[0])
