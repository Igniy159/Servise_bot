from core.ticket_core import User
from core.actions import Actions, ConfirmAction, CloseAction, PriorityAction, AssignAction, OnWaitAction, \
    OffWaitAction, FinishAction, RejectAction


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

