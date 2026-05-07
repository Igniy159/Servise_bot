from  core.ticket_core import User,Ticket
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

class EventUser:
    def __init__(self,actor: User, user: User, action:str):
        self.actor = actor
        self.user = user
        self.action = action

class EventGetUser:
    def __init__(self, actor: User, users: list[dict]):
        self.actor = actor
        self.users = users

class EventBranch:
    def __init__(self, user: User, branch:dict, action: str):
        self.user = user
        self.branch = branch
        self.action = action
class EventGetBranch:
    def __init__(self,user: User, branches:list[dict]):
        self.user = user
        self.branches = branches
