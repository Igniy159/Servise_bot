from  core.ticket_core import User,Ticket
from policy.policy_ticket import Actions


class EventCreateTicket:
    def __init__(self, creator: User, ticket: Ticket):
        self.user = creator
        self.ticket = ticket
class EventApplyTicket:
    def __init__(self, actor: User, updated_ticket:Ticket, action: Actions):
        self.user = actor
        self.ticket = updated_ticket
        self.action = action
class EventGetTicket:
    def __init__(self, tickets: list[dict]):
        self.tickets = tickets
class EventGetHistory:
    def __init__(self, history: list[dict]):
        self.history = history
