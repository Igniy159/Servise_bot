from core.enums import Role
from core.ticket_core import User, RuleAlert
from core.actions import Actions, ConfirmAction, CloseAction, PriorityAction, AssignAction, OnWaitAction, \
    OffWaitAction, FinishAction, RejectAction
from repository.unit_of_work import UoW


class Recipient:
    def __init__(self, creator: User):
        self.me = creator

class RecipientsCreateTicket(Recipient):
    def __init__(self, creator: User, recipient: dict):
        super().__init__(creator)
        self.target = recipient['target']
        self.manager = recipient['manager']

class RecipientsApplyTicket(Recipient):
    def __init__(self, creator: User, action:Actions, context:dict):
        super().__init__(creator)
        self.action = action
        self.context = context
        self._find_recipient()

    def _find_recipient(self):
        link_depart = {
            ConfirmAction,
            PriorityAction,
            CloseAction,
            RejectAction
        }
        link_manager = {
            AssignAction,
            OnWaitAction,
            OffWaitAction,
            FinishAction,
            RejectAction
        }
        if self.action in link_depart:
            self.target = self.context['depart']
        if self.action in link_manager:
            self.target += self.context['manager']

class RecipientResolver:
    @staticmethod
    def get_alert_recipients(uow: UoW, actor: User, alert_rule: RuleAlert)-> list[User]:
        recipients = []
        if actor.role == Role.EMPLOYEE:
            role_id = uow.role_mapper.get_roles_id(Role.MANAGER)
            recipients.append(uow.users.get({'branch_id': actor.branch_id,
                                                  'role_id': role_id}))
        depart_user = uow.users.get({"depart_id": alert_rule.target.id})
        if depart_user:
            recipients.append(depart_user)
        else:
            owner_id = uow.role_mapper.get_roles_id(Role.OWNER)
            owner = uow.users.get({'role_id': owner_id})
            recipients.append(owner)
        return recipients
