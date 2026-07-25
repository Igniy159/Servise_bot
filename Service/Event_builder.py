from core.ticket_core import User,Ticket
from core.actions import Actions


class EventCreateTicket:
    def __init__(self, actor: User, ticket: Ticket):
        self.actor = actor
        self.ticket = ticket
class EventApplyTicket:
    def __init__(self, actor: User, updated_ticket:Ticket, action: Actions):
        self.actor = actor
        self.ticket = updated_ticket
        self.action = action
class EventGetTicket:
    def __init__(self,actor: User, tickets: list[dict]):
        self.actor = actor
        self.tickets = tickets
class EventGetHistory:
    def __init__(self,actor: User, history: list[dict]):
        self.actor = actor
        self.history = history

