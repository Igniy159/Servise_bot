from datetime import datetime
from typing import Optional
from core.exceptions import CoreValidationBreak, PermissionDenied, LifecycleError
from core.enums import State, Role, TypeTicket, KindRule, ClassTicket, ClassAlert, DATE_FORMAT


class Permission:
    def __init__(self, permissions:dict):
        self.permissions = permissions

    def __call__(self, role: Role):
        return self.permissions.get(role.name,{})

    def can(self,
            actor:User,
            type_action: str,
            action: str):
        access = self.permissions[actor.role.name]['permissions']
        if type_action not in {'lead_branch', 'lead_user', 'lead_ticket'}:
            raise CoreValidationBreak
        if not access[type_action].get(action, None):
            raise PermissionDenied(f"{actor.role.name} not access on this action {action}")

class TicketLifecycle:
    def __init__(self, raw_config:dict):
        ticket_fsm = raw_config['ticket_lifecycle']

        self.fsm  = ticket_fsm

    def next_step(self, state: State):
        return self.fsm.get(state.name, None)

    def check_prohibit_step(self, first_state: State, second_state:State):
        next_state =  self.next_step(first_state)
        if not next_state:
            raise LifecycleError
        if second_state not in next_state:
            raise LifecycleError

class Branch:
    def __init__(self,
                 branch_id:int,
                 branch_name:str):
        self.id = branch_id
        self.name = branch_name

    @classmethod
    def for_db(cls, branch_dict: dict)-> Branch:
        return cls(branch_id= branch_dict['branch_id'],
                    branch_name= branch_dict['branch_name'])

    def __str__(self):
        return f"Филиал №{self.id} {self.name} "

class Department:
    def __init__(self, depart_id: int, depart_name:str):
        self.id = depart_id
        self.name = depart_name

    @classmethod
    def for_db(cls, depart_dict: dict):
        return cls(depart_dict['depart_id'],
                   depart_dict['depart_name'])

    def __str__(self):
        return f"Отдел {self.name} "

class User:
    __doc__ = "This class for user operations"

    def __init__(self,
                 user_id: int,
                 user_name: str,
                 api_id : int,
                 role: Role,
                 depart : Optional[Department]= None,
                 branch: Optional[Branch] = None):
        self.id = user_id
        self.name = user_name
        self.api_id = api_id
        self.role = role
        self.depart_id = depart.id if depart else None
        self.depart_name = depart.name if depart else  None
        self.branch_id = branch.id if branch else None
        self.branch_name = branch.name if branch else None


    @classmethod
    def for_db(cls, user_dict: dict)->User:
        depart_id = user_dict.get('depart_id', None)
        depart_name = user_dict.get('depart_name', None)
        branch_id = user_dict.get('branch_id', None)
        branch_name = user_dict.get('branch_name', None)
        depart = branch = None
        if depart_name and depart_id:
            depart = Department(depart_id,depart_name)
        if branch_id and branch_name:
            branch = Branch(branch_id,branch_name)
        return cls(user_id = user_dict['user_id'],
                            user_name= user_dict['user_name'],
                            api_id= user_dict['api_user_id'],
                            role= Role(user_dict['role_name']),
                            depart = depart,
                            branch = branch)

    def __str__(self):
        return f"{self.name}|{self.role.name}|{self.depart_name or self.branch_name or ' '}"

class Alert:
    def __init__(self,
                 actor_id: int,
                 branch_id: int,
                code_alert: int,
                 comment: str,
                date_create: Optional[str] =None):
        self.actor_id = actor_id
        self.branch_id = branch_id
        if not date_create:
            self.date_create = datetime.now().strftime(DATE_FORMAT)
        self.code_alert = code_alert
        self.comment = comment

    @classmethod
    def for_db(cls,alert_dict: dict)->Alert:
        return cls(alert_dict['actor_id'],
                   alert_dict['branch_id'],
                    alert_dict['code_alert'],
                   alert_dict['comment'],
                   alert_dict['date_create'])

class Rule:
    def __init__(self,
                 code: int,
                 kind: KindRule,
                 class_rule: ClassTicket| ClassAlert,
                 name: str,
                 target: Department):
        self.kind = kind
        self.code = code
        self.class_rule = class_rule
        self.name = name
        self.target = target

    @classmethod
    def for_db(cls, data: dict):
        kind = KindRule(data['kind'])
        if kind == KindRule.ALERT:
            class_rule = ClassAlert(data['class'])
        else:
            class_rule = ClassTicket(data['class'])
        return cls(data['code'],
                    kind,
                   class_rule,
                   data['name'],
                   Department(data['target_id'],
                   data['target_name']))

    def __str__(self):
        return f'{self.code},{self.name},{self.class_rule}'

class TicketContext:
    def __init__(self,
                 actor_id: int,
                 branch_id: int,
                 comment: str,
                 severity: TypeTicket,
                 file_id: Optional[int]= None):
        self.severity = severity
        self.actor_id = actor_id
        self.branch_id = branch_id
        self.comment = comment
        self.file_id = file_id

class Ticket:
    def __init__(self,
                 code_ticket: int,
                 state: State,
                 context: TicketContext,
                 ticket_id: Optional[int]=None,
                 assigned_to_id: Optional[int]=None,
                 date_create: Optional[str]=None):
        self.id = ticket_id
        self.code = code_ticket
        self.state = state
        self.context = context
        self.assigned_to = assigned_to_id
        self.date_create = date_create

    @classmethod
    def for_db(cls, ticket: dict):
        return cls(
            ticket['code_ticket'],
            State(ticket['ticket_state']),
            TicketContext(ticket['actor_id'],
                          ticket['branch_id'],
                          ticket['comment'],
                          TypeTicket(ticket['severity']),
                          ticket.get('file_id')),
            ticket.get('ticket_id'),
            ticket.get('assigned_to'),
            ticket['date_create'])

class TicketView:
    def __init__(self,
                 ticket: Ticket,
                 rule_name: str,
                 branch_name: str):
        self.ticket = ticket
        self.rule_name = rule_name
        self.branch_name = branch_name

    def __str__(self):
        return "\n".join([
            f"📌 {self.rule_name}",
            f"💬 {self.ticket.context.comment}",
            f"🏢 {self.branch_name}",
            f"🕒 {self.ticket.date_create}",
        ])

    @classmethod
    def for_db(cls, ticket: dict):
        return cls(Ticket.for_db(ticket),
                   ticket['rule_name'],
                   ticket['branch_name'])