from datetime import datetime
from typing import Optional
from api.command import CmdCreateTicket
from logger.logger import core_logger
from core.exceptions import CoreValidationBreak, LifecycleError
from core.actions import (Actions, ConfirmAction,
                          RejectAction, AssignAction,
                          OffWaitAction, OnWaitAction,
                        CloseAction, FinishAction,
                        PriorityAction)
from core.enums import State, Role


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
        return f"{self.name}|{self.role.name}|{self.depart_name or self.branch_name or " "}"

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
            f = "%Y-%m-%d %H:%M:%S"
            self.date_create = datetime.now().strftime(f)
        self.code_alert = code_alert
        self.comment = comment

    @classmethod
    def for_db(cls,alert_dict: dict)->Alert:
        return cls(alert_dict['actor_id'],
                   alert_dict['branch_id'],
                    alert_dict['code_alert'],
                   alert_dict['comment'],
                   alert_dict['date_create'])

class RuleAlert:
    def __init__(self,
                 code_alert: int,
                 class_alert: str,
                 name_alert: str,
                 target: Department):
        self.code_alert = code_alert
        self.class_alert = class_alert
        self.name_alert = name_alert
        self.target = target

    @classmethod
    def for_db(cls, data: dict):
        return cls(data['code_alert'],
                   data['class_alert'],
                   data['name_alert'],
                   Department(data['target_id'],
                   data['target_name']))

    def __str__(self):
        return f'{self.code_alert},{self.name_alert},{self.class_alert}'

class Ticket:
    __doc__ = "This class for ticket field validations and patch operations."

    def __init__(self, data: dict):
        self.ticket_id = data.get('ticket_id', None)
        self.creator_id = data.get('creator_id')
        self.creator_name = data.get('creator_name')
        self.branch_id = data.get('branch_id')
        self.branch_name = data.get('branch_name')
        self.event_type = data.get('event_type')
        self.problem_category = data.get('problem_category')
        self.problem_name = data.get('problem_name')
        self.problem_class = data.get('problem_class')
        self.problem_type = data.get('problem_type')
        self.zone = data.get('zone')
        self.scenario = data.get('scenario')
        self.target = data.get('target')
        self.date_create = data.get('date_create')
        self.sla_reaction_deadline = data.get('sla_reaction_deadline')
        self.sla_resolution_deadline = data.get('sla_resolution_deadline')
        self.date_close = data.get('date_close')
        self.assigned_to = data.get('assigned_to')
        self.reject_comment = data.get('reject_comment')
        self.comment = data.get('comment')
        self.priority = data.get('priority')
        self.current_state = data.get('current_state')
        self.history = []

    @classmethod
    def from_created(
            cls,
            cmd: CmdCreateTicket,
            resolve: dict,
            user: User) -> Ticket:
        now = datetime.now()
        date = {
            'creator_id': user.id,
            'creator_name': user.name,
            'branch_id': user.branch_id or cmd.branch_id,
            'branch_name': user.branch_name or resolve['branch_name'],
            'event_type': cmd.event_type,
            'problem_category': cmd.problem_category,
            'problem_name': cmd.problem_name,
            'problem_class': cmd.problem_class,
            'problem_type': cmd.problem_type,
            'zone': cmd.zone,
            'scenario': resolve['scenario'],
            'target': resolve['target'],
            'date_create': now,
            'sla_reaction_deadline': resolve['react_time'],
            'sla_resolution_deadline': resolve['resol_time'],
            'date_close': None,
            'assigned_to': None,
            'reject_comment': None,
            'comment': cmd.comment,
            "priority": cmd.priority or resolve['priority'],
            "current_state": None,
            'history': []
        }

        return cls(date)

    @classmethod
    def from_data_base(cls,
                       ticket: dict):
        return cls(ticket)

    @staticmethod
    def for_data_base(ticket, enum: dict) -> dict:
        priority_map = enum['priority']
        state_map = enum['TICKET_STATUS']
        depart_map = enum['DEPARTMENTS']
        f = "%Y-%m-%d %H:%M:%S"

        res = {'ticket_id': getattr(ticket, 'ticket_id', None),
               'creator_id': ticket.creator_id,
               'branch_id': ticket.branch_id,
               'event_type': ticket.event_type,
               'problem_category': ticket.problem_category,
               'problem_name': ticket.problem_name,
               'problem_class': ticket.problem_class,
               'problem_type': ticket.problem_type,
               'zone': ticket.zone,
               'scenario': ticket.scenario,
               'target': depart_map.get(ticket.target),
               'date_create': ticket.date_create.strftime(f),
               'sla_reaction_deadline': ticket.sla_reaction_deadline.strftime(
                   f) if ticket.sla_reaction_deadline else None,
               'sla_resolution_deadline': ticket.sla_resolution_deadline.strftime(
                   f) if ticket.sla_resolution_deadline else None,
               'current_state': str(state_map.get(ticket.current_state)),
               'date_close': ticket.date_close.strftime(f) if ticket.date_close else None,
               'assigned_to': ticket.assigned_to,
               'reject_comment': ticket.reject_comment,
               'comment': ticket.comment,
               'priority': priority_map.get(ticket.priority)}
        return res

    def update_solution(self, solution: dict) -> Ticket:
        self.current_state = solution['current_state']
        self.target = solution.get('target', self.target)
        self.assigned_to = solution.get('assigned_to', None)
        return self

    def validate_sla(self):
        if self.sla_reaction_deadline is not None:
            if self.sla_reaction_deadline < self.date_create:
                raise CoreValidationBreak("Reaction SLA before creation date")
        if self.sla_resolution_deadline is not None:
            if self.sla_resolution_deadline < self.date_create:
                raise CoreValidationBreak("Resolution SLA before creation date")
        if self.sla_resolution_deadline < self.sla_reaction_deadline:
            raise CoreValidationBreak("Resolution SLA before reaction SLA date")

    def _validate_fsm(self):
        if self.date_close:
            if self.current_state not in (State.CLOSED, State.CANCELLED):
                raise LifecycleError(f"{self.date_close} status not CLOSED or CANCELLED")
        if self.reject_comment and self.current_state != State.CANCELLED:
            raise LifecycleError(f"{self.reject_comment} status not CANCELLED")
        if self.assigned_to and self.current_state in (State.NEW, State.CONFIRMED):
            raise LifecycleError(f"{self.assigned_to} status {self.current_state} incorrect ")
        if self.current_state in (State.CLOSED, State.CANCELLED) and not self.date_close:
            raise LifecycleError("Closed ticket without date_close")

    def _apply_action(self, action: Actions, state: State= None):
        if state:
            self._log_history('current_state',self.current_state,str(state))
            self.current_state = state
        allowed_field = {'comment',
                         'reject_comment',
                         'priority',
                         'date_close',
                         'assigned_to'}
        for field, value in action.cmd.items():
            if field in allowed_field:
                if getattr(self,field) != value:
                    self._log_history(field,getattr(self,field),value)
                    setattr(self,field,value)
        return self

    def _log_history(self, field:str, old: str, new: str) -> None:
        self.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "changes": field,
            "old": old,
            "new": new})

    def _fsm(self, action: Actions, fsm_config: dict) -> State:
        current_state = self.current_state
        allowed_state = fsm_config[current_state]['next']
        mapper_actions = {
            ConfirmAction: State.CONFIRMED,
            RejectAction: State.CANCELLED,
            AssignAction: State.IN_PROGRESS,
            OnWaitAction: State.WAITING_EXTERNAL,
            OffWaitAction: State.IN_PROGRESS,
            FinishAction: State.RESOLVED,
            CloseAction: State.CLOSED}
        for field, value in mapper_actions.items():
            if isinstance(action, field):
                next_state = value
                break
        else:
            raise LifecycleError("Unknown action")

        if next_state in allowed_state:
            return next_state
        raise LifecycleError('Incorrect action')

    def update_ticket(self, fsm, action: Actions):
        try:
            if not isinstance(action,PriorityAction):
                state = self._fsm(action, fsm)
                self._apply_action(action, state)
                self._validate_fsm()
            else:
                self._apply_action(action)

        except CoreValidationBreak:
            raise
        except LifecycleError:
            raise
        core_logger.info(f"Ticket {self.ticket_id} update patch {action}")
        return self
