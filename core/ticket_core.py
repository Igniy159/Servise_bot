from datetime import datetime
from api.command import CmdCreateTicket
from logger.logger import core_logger
from core.exceptions import CoreValidationBreak, LifecycleError
from core.actions import (Actions, ConfirmAction,
                          RejectAction, AssignAction,
                          OffWaitAction, OnWaitAction,
                        CloseAction, FinishAction,
                        PriorityAction)
from enum import Enum,auto



def string_shema_validator(config: dict) -> None:
    enum_classes = config['enum']
    matrix = config['priority_matrix']
    for classes, problems in matrix['OBJECT_CLASSES'].items():
        if classes not in enum_classes['OBJECT_CLASSES']:
            raise CoreValidationBreak(f"Error in priority_matrix_OBJECT_CLASSES: {classes}")
        for problem, two_keys in problems.items():
            if problem not in enum_classes["PROBLEMS"]:
                raise CoreValidationBreak(f"Error in priority_matrix_PROBLEMS: {problem}")
            elif type(two_keys) != dict:
                raise CoreValidationBreak("Incorrect type in priority_matrix")
            elif set(two_keys.keys()) != {'priority', 'scenario'}:
                raise CoreValidationBreak(f"Incorrect type in priority_matrix: {two_keys.keys()}")
            elif two_keys['priority'] not in enum_classes['priority']:
                raise CoreValidationBreak(f"Error in priority_matrix_priority: {two_keys['priority']}")
            elif two_keys['scenario'] not in enum_classes['SCENARIOS']:
                raise CoreValidationBreak(f"Error in priority_matrix_SCENARIOS: {two_keys['scenario']}")

    r_alert = config['rules_alert']
    for type_alert, two_keys in r_alert.items():
        if type_alert not in enum_classes['CLASS_ALERTS']:
            raise CoreValidationBreak(f"Error in rules_alert_type: {type_alert}")
        elif set(two_keys.keys()) != {'target', 'scenario'}:
            raise CoreValidationBreak(f"Incorrect type in rules_alert: {two_keys.keys()}")
        elif two_keys['scenario'] not in enum_classes["SCENARIOS"]:
            raise CoreValidationBreak(f"Error in rules_alert_scenario: {two_keys['scenario']}")
        elif two_keys['target'] not in enum_classes["DEPARTMENTS"]:
            raise CoreValidationBreak(f"Error in rules_alert_target: {two_keys['target']}")

    r_request = config['rules_request']['REQUEST_CLASSES']
    for classes, problems in r_request.items():
        if classes not in enum_classes['REQUEST_CLASSES']:
            raise CoreValidationBreak(f"Error in rules_request_CLASSES: {classes}")
        if problems['target'] not in enum_classes["DEPARTMENTS"]:
            raise CoreValidationBreak(f"Error in rules_request_target: {problems['target']}")
        for type_problem, two_keys in problems.items():
            if type_problem in ['description', "target"]:
                continue
            elif type_problem not in enum_classes["TYPE_REQUEST"]:
                raise CoreValidationBreak(f"Error in rules_request_type_problem: {type_problem}")
            elif type(two_keys) != dict:
                raise CoreValidationBreak(f"Incorrect type in rules_request")
            elif set(two_keys.keys()) != {'scenario', 'priority'}:
                raise CoreValidationBreak(f"Incorrect type in rules_request: {two_keys.keys()}")
            elif two_keys['priority'] not in enum_classes["priority"]:
                raise CoreValidationBreak(f"Error in rules_request_priority: {two_keys['priority']}")
            elif two_keys['scenario'] not in enum_classes['SCENARIOS']:
                raise CoreValidationBreak(f"Error in rules_request_SCENARIOS: {two_keys['scenario']}")

    depart = config['departments']['DEPARTMENTS']
    for dep, role in depart.items():
        if dep not in enum_classes['DEPARTMENTS']:
            raise CoreValidationBreak(f"Error in DEPARTMENTS: {dep}")
        if role['role'] not in enum_classes['ROLES']:
            raise CoreValidationBreak(f"Error in DEPARTMENTS_roles: {role['role']}")

    role = config['roles']["ROLES"]
    for type_role, key_role in role.items():
        if type_role not in enum_classes["ROLES"]:
            raise CoreValidationBreak(f" Error in roles: {type_role}")
        elif 'permissions' not in key_role.keys():
            raise CoreValidationBreak(f" Error this roles: {type_role} Not permissions")
        elif set(key_role["permissions"]) != set(enum_classes['ROLES_PERMISSION']):
            print(set(key_role["permissions"]), 'права')
            print(set(enum_classes['ROLES_PERMISSION']), 'словарь')
            raise CoreValidationBreak(f" Error this roles: {type_role} incorrect permissions")

    ars_object = config['object']["ARS_OBJECT"]
    for zones, zone_obj in ars_object.items():
        if zones not in enum_classes["zones"]:
            raise CoreValidationBreak(f" Error in object: {zones} incorrect")
        elif not isinstance(zone_obj, dict):
            raise CoreValidationBreak(f" Error in object: {zone_obj} incorrect type")
        for obj_name, obj_data in zone_obj.items():
            if "class" not in obj_data:
                raise CoreValidationBreak(f"Error in object '{obj_name}': missing 'class'")
            obj_class = obj_data["class"]
            if obj_class not in enum_classes["OBJECT_CLASSES"]:
                raise CoreValidationBreak(
                    f"Error in object '{obj_name}': "
                    f"unknown class '{obj_class}'"
                )

    req = config["request"]
    for class_req, type_req in req.items():
        if class_req not in enum_classes["REQUEST_CATEGORY"]:
            raise CoreValidationBreak(f"This class_request {class_req} incorrect")
        elif not isinstance(type_req, dict):
            raise CoreValidationBreak(f"This type_request {type_req} incorrect ")
        for name_req, data_req in type_req.items():
            if "class" not in data_req:
                raise CoreValidationBreak(f"Error in object '{data_req}': missing 'class'")

            class_req = data_req["class"]
            if class_req not in enum_classes["REQUEST_CLASSES"]:
                raise CoreValidationBreak(
                    f"Error in object '{name_req}': "
                    f"unknown class '{class_req}'"
                )

    al = config["alerts"]
    for category, type_al in al.items():
        if category not in enum_classes['CATEGORY_ALERTS']:
            raise CoreValidationBreak(f" This category {category} incorrect")
        for name, key_al in type_al.items():
            if not isinstance(key_al, dict):
                raise CoreValidationBreak(f" This {key_al} incorrect type")
            elif 'class' not in key_al:
                raise CoreValidationBreak(f" This {key_al} missing class")
            class_al = key_al["class"]
            if class_al not in enum_classes["CLASS_ALERTS"]:
                raise CoreValidationBreak(
                    f"Error in object '{name}': "
                    f"unknown class '{class_al}'"
                )

    life = config['ticket_lifecycle']["NORMAL_LIFECYCLE"]
    life_admin = config['ticket_lifecycle']["ADMIN_LIFECYCLE"]
    for key, val in life.items():
        if key not in enum_classes["TICKET_STATUS"]:
            raise CoreValidationBreak(f"{key} not in lifecycle ticket")
        for name, step in val.items():
            if name != "next":
                raise CoreValidationBreak(f"{name} Incorrect name in lifecycle ticket")
            if step is None:
                continue
            elif set(step) - set(enum_classes["TICKET_STATUS"]):
                raise CoreValidationBreak(f" {step} Incorrect name in lifecycle ticket")

    for key, val in life_admin.items():
        if key not in enum_classes["TICKET_STATUS"]:
            raise CoreValidationBreak(f"{key} not in lifecycle ticket")
        for name, step in val.items():
            if name != "next":
                raise CoreValidationBreak(f"{name} Incorrect name in lifecycle ticket")
            if step is None:
                continue
            elif set(step) - set(enum_classes["TICKET_STATUS"]):
                raise CoreValidationBreak(f" {step} Incorrect name in lifecycle ticket")

    sla = config['SLA']['SLA_POLICIES']
    for key, val in sla.items():
        if key not in enum_classes["SLA_TYPE"]:
            raise CoreValidationBreak(f"{key} incorrect SLA type")
        for i, j in val.items():
            if i not in ("reaction", 'resolution'):
                raise CoreValidationBreak(f"{i} SLA incorrect value")
            elif j is None:
                continue
            a = j[-1]
            if a not in ("m", "d", "h"):
                raise CoreValidationBreak(f"{j} SLA incorrect value")
    core_logger.info("Config correct")


class State(Enum):
    NEW = auto()
    CONFIRMED = auto()
    IN_PROGRESS = auto()
    WAITING_EXTERNAL = auto()
    RESOLVED = auto()
    CLOSED = auto()
    CANCELLED = auto()


class User:
    __doc__ = "This class for user operations"

    def __init__(self, user: dict):
        self.id = user['user_id']
        self.name = user['user_name']
        self.api_id = user['api_user_id']
        self.role = user['role_name']
        self.depart_id = user.get('depart_id', None)
        self.depart_name = user.get('depart_name', None)
        self.branch_id = user.get('branch_id', None)
        self.branch_name = user.get('branch_name', None)


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

        res = {'ticket_id': getattr(ticket, 'ticket_id', None),
               'creator_id': ticket.creator_id,
               'branch_id': ticket.branch_name,
               'event_type': ticket.event_type,
               'problem_category': ticket.problem_category,
               'problem_name': ticket.problem_name,
               'problem_class': ticket.problem_class,
               'problem_type': ticket.problem_type,
               'zone': ticket.zone,
               'scenario': ticket.scenario,
               'target': depart_map.get(ticket.target),
               'date_create': ticket.date_create.strftime("%Y-%m-%d %H:%M:%S"),
               'sla_reaction_deadline': ticket.sla_reaction_deadline.strftime(
                   "%Y-%m-%d %H:%M:%S") if ticket.sla_reaction_deadline else None,
               'sla_resolution_deadline': ticket.sla_resolution_deadline.strftime(
                   "%Y-%m-%d %H:%M:%S") if ticket.sla_resolution_deadline else None,
               'current_state': str(state_map.get(ticket.current_state)),
               'date_close': ticket.date_close.strftime("%Y-%m-%d %H:%M:%S") if ticket.date_close else None,
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
