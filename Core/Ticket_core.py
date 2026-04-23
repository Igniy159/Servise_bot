from copy import deepcopy
from datetime import datetime, timedelta
from typing import Optional
from Logger.logger import core_logger
import copy
from Core.exceptions import TicketError,CoreValidationBreak,LifecycleError



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
            elif set(two_keys.keys()) != {'priority','scenario'}:
                raise CoreValidationBreak(f"Incorrect type in priority_matrix: {two_keys.keys()}")
            elif two_keys['priority'] not in enum_classes['priority']:
                raise CoreValidationBreak(f"Error in priority_matrix_priority: {two_keys['priority']}")
            elif two_keys['scenario'] not in enum_classes['SCENARIOS']:
                raise CoreValidationBreak(f"Error in priority_matrix_SCENARIOS: {two_keys['scenario']}")

    r_alert = config['rules_alert']
    for type_alert, two_keys in r_alert.items():
        if type_alert not in enum_classes['CLASS_ALERTS']:
            raise CoreValidationBreak(f"Error in rules_alert_type: {type_alert}")
        elif set(two_keys.keys()) != {'target','scenario'}:
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
            print(set(key_role["permissions"]),'права')
            print(set(enum_classes['ROLES_PERMISSION']),'словарь')
            raise CoreValidationBreak(f" Error this roles: {type_role} incorrect permissions")

    ars_object = config['object']["ARS_OBJECT"]
    for zones, zone_obj in ars_object.items():
        if zones not in enum_classes["zones"]:
            raise CoreValidationBreak(f" Error in object: {zones} incorrect")
        elif not isinstance(zone_obj,dict):
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
        elif not isinstance(type_req,dict):
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
            if i not in ("reaction",'resolution'):
                raise CoreValidationBreak(f"{i} SLA incorrect value")
            elif j is None:
                continue
            a = j[-1]
            if a not in ("m","d","h"):
                raise CoreValidationBreak(f"{j} SLA incorrect value")
    core_logger.info("Config correct")

def validate_event(event: dict, config: dict) -> None:
    if "type" not in event or event['type'] not in config['enum']['TYPE_EVENT']:
        raise CoreValidationBreak("Incorrect type")
    if 'problem_category' not in event or event['problem_category'] is None:
        raise CoreValidationBreak("Incorrect problem_category")
    if 'problem_name'not in event or event['problem_name'] is None:
        raise CoreValidationBreak("Incorrect problem_name")
    if 'problem_class' not in event or event['problem_class'] is None:
        raise CoreValidationBreak("Incorrect problem_class")
    if ('problem_type' not in event or event['problem_type'] is None) and event["type"] != "ALERT":
        raise CoreValidationBreak("Incorrect 'problem_type'")

    if event["type"] == "OBJECT_PROBLEM":
        validate_object(event,config)
    elif event["type"] == "REQUEST":
        validate_request(event,config)
    elif event['type'] == "ALERT":
        validate_alert(event,config)
    core_logger.info(f"Event {event['problem_name']} correct")

def validate_object(event: dict,config:dict):
    if event['problem_class'] not in config["enum"]['OBJECT_CLASSES']:
        raise CoreValidationBreak(f"INCORRECT OBJECT_CLASS - {event['problem_class']}")
    elif event['problem_class'] not in config["priority_matrix"]['OBJECT_CLASSES']:
        raise CoreValidationBreak(f"INCORRECT OBJECT_CLASS - {event['problem_class']}")

    elif event['problem_type'] not in config["enum"]["PROBLEMS"]:
        raise CoreValidationBreak(f"INCORRECT type_problem - {event['problem_type']}")
    elif event['problem_type'] not in config["priority_matrix"]['OBJECT_CLASSES'][event['problem_class']]:
        raise CoreValidationBreak(f"INCORRECT type_problem - {event['problem_type']}")

    elif event['problem_category'] not in config["enum"]["zones"]:
        raise CoreValidationBreak(f"INCORRECT type_problem - {event['problem_category']}")

    if "zone" not in event or event["zone"] is None:
        raise CoreValidationBreak("Incorrect zone")
    elif event["zone"] not in config["enum"]["zones"]:
        raise CoreValidationBreak(f"INCORRECT zone - {event['zone']}")
    elif event["zone"] not in config["object"]["ARS_OBJECT"]:
        raise CoreValidationBreak(f"INCORRECT zone - {event['zone']}")

    elif event['problem_name'] not in config["object"]["ARS_OBJECT"][event['zone']]:
        raise CoreValidationBreak(f"INCORRECT problem - {event['problem_name']}")

    if config['object']['ARS_OBJECT'][event['zone']][event['problem_name']]['class'] != event["problem_class"]:
        raise CoreValidationBreak(f"Incorrect class - {event['problem_class']}")
    elif event['problem_name'] not in config['object']['ARS_OBJECT'][event['zone']]:
        raise CoreValidationBreak(f"Incorrect name - {event['problem_name']}")
    elif event['zone'] != event["problem_category"]:
        raise CoreValidationBreak(f"Incorrect zone - {event['zone']}")

def validate_request(event: dict,config:dict):
    if event['problem_class'] not in config["enum"]['REQUEST_CLASSES']:
        raise CoreValidationBreak(f"INCORRECT request_class - {event['problem_class']}")
    elif event['problem_class'] not in config["rules_request"]["REQUEST_CLASSES"]:
        raise CoreValidationBreak(f"INCORRECT request_class - {event['problem_class']}")

    if event['problem_type'] not in config['enum']['TYPE_REQUEST']:
        raise CoreValidationBreak(f"INCORRECT request_type - {event['problem_type']}")
    elif event['problem_type'] not in config["rules_request"]["REQUEST_CLASSES"][event['problem_class']]:
        raise CoreValidationBreak(f"INCORRECT request_type - {event['problem_type']}")

    if event['problem_category'] not in config["enum"]["REQUEST_CATEGORY"]:
        raise CoreValidationBreak(f"INCORRECT request_category - {event['problem_category']}")

    elif event['problem_name'] not in config['request'][event['problem_category']]:
        raise CoreValidationBreak(f"INCORRECT request - {event['problem_name']}")

    if event['problem_class'] != config['request'][event['problem_category']][event['problem_name']]['class']:
        raise CoreValidationBreak(f"INCORRECT request_class - {event['problem_class']}")
    elif event['problem_name'] not in config['request'][event['problem_category']]:
        raise CoreValidationBreak(f"INCORRECT request_name - {event['problem_name']}")

def validate_alert(event: dict,config:dict):
    if event.get("problem_type") is not None:
        raise CoreValidationBreak("ALERT must not contain problem_type")

    if event['problem_class'] not in config['enum']['CLASS_ALERTS']:
        raise CoreValidationBreak(f"INCORRECT alert_class - {event['problem_class']}")
    elif event['problem_class'] not in config["rules_alert"]:
        raise CoreValidationBreak(f"INCORRECT alert_class - {event['problem_class']}")

    if event['problem_category'] not in config['enum']['CATEGORY_ALERTS']:
        raise CoreValidationBreak(f"INCORRECT alert_category - {event['problem_category']}")
    elif event['problem_category'] not in config["alerts"]:
        raise CoreValidationBreak(f"INCORRECT alert_category - {event['problem_category']}")

    if event['problem_class'] != config['alerts'][event['problem_category']][event['problem_name']]['class']:
        raise CoreValidationBreak(f"INCORRECT alert_problem - {event['problem_class']}")
    if event['problem_name'] not in config['alerts'][event['problem_category']]:
        raise CoreValidationBreak(f"INCORRECT alert_problem - {event['problem_name']}")


def resolve_decision(event_data: dict, config: dict)-> dict:

    res_dict = deepcopy(event_data)

    if event_data["type"] == "OBJECT_PROBLEM":
        matrix = config["priority_matrix"]['OBJECT_CLASSES'][event_data['problem_class']][event_data['problem_type']]
        res_dict["priority"] = matrix["priority"]
        res_dict["scenario"] = matrix["scenario"]
        res_dict["target"] = 'ARS'  #target object only ARS

    elif event_data["type"] == "REQUEST":
        req = config["rules_request"]['REQUEST_CLASSES'][event_data['problem_class']][event_data['problem_type']]
        res_dict["priority"] = req["priority"]
        res_dict["scenario"] = req["scenario"]
        res_dict["target"] = config["rules_request"]['REQUEST_CLASSES'][event_data["problem_class"]]["target"]

    elif event_data['type'] == "ALERT":
        al = config['rules_alert'][event_data['problem_class']]
        res_dict["scenario"] = al["scenario"]
        res_dict["target"] = al["target"]

    return res_dict


def path_shema_validator(path: dict, role:str, ticket:dict, config: dict,type_fsm:dict)-> None:
    for field in path:
        if field not in config['ticket']['TICKET']['mutable']:
            raise CoreValidationBreak(f"{field} not mutable type")
    if role not in config['enum']['ROLES']:
        raise CoreValidationBreak(f"{role} incorrect type")
    if ticket['event_type'] == "ALERT":
        raise CoreValidationBreak("ALERT not mutable type")

    actual_state = ticket['current_state']
    if 'current_state'in path:
        actual_state = path['current_state']
        if path['current_state'] not in type_fsm:
            raise CoreValidationBreak(f"{path['current_state']} incorrect type")
        life = type_fsm
        next_states = life[ticket["current_state"]]['next'] or []

        if path['current_state'] not in next_states:
            raise LifecycleError("Invalid lifecycle transition")

    if actual_state in ("CLOSED", "CANCELLED") and "date_close" not in path:
        raise LifecycleError("Closing ticket requires date_close")

    if 'date_close' in path:
        if  not isinstance(path['date_close'],datetime):
            raise CoreValidationBreak(f" This {path['date_close']} incorrect type")
        if actual_state not in ('CLOSED', 'CANCELLED'):
            raise LifecycleError(f" This {path['date_close']} incorrect on step {actual_state}")

    if 'assigned_to' in path:
        if not isinstance(path['assigned_to'], int):
            raise CoreValidationBreak(f" This {path['assigned_to']} incorrect type")
        if actual_state != 'IN_PROGRESS':
            raise LifecycleError(f" This {path['assigned_to']} incorrect on step {actual_state}")

    if 'priority' in path:
        if not isinstance(path['priority'], str):
            raise CoreValidationBreak(f" This {path['priority']} incorrect type")
        if actual_state != 'CONFIRMED' and not config['roles']["ROLES"][role]['permissions']['extra_change_priority']:
            raise LifecycleError(f" This {path['priority']} incorrect on step {actual_state}")

    if 'comment' in path:
        if path['comment'] and not isinstance(path['comment'], (str,type(None))):
            raise CoreValidationBreak(f" This {path['comment']} incorrect type")

    if actual_state == "CANCELLED" and "reject_comment" not in path:
        raise CoreValidationBreak("Cancel requires reject_comment")

    if 'reject_comment' in path:
        if not isinstance(path['reject_comment'], str):
            raise CoreValidationBreak(f" This {path['reject_comment']} incorrect type")
        if  actual_state != 'CANCELLED':
            raise LifecycleError(f" This {path['reject_comment']} incorrect on step {actual_state}")
    core_logger.info("path_correct")


def encode_ticket_validator(ticket:dict)-> None:
    required_fields = ['creator_id', 'branch_id','event_type','problem_category',
    'problem_name','problem_class','problem_type','zone','scenario','target',
        'date_create','sla_reaction_deadline','sla_resolution_deadline',
        'date_close','assigned_to','reject_comment','comment',
        "priority","current_state",'history']

    for field in required_fields:
        if field not in ticket:
            raise CoreValidationBreak(f"This {field} not in ticket")
    type_map= {
        'creator_id': int,
        'branch_id': int,
        'event_type': str,
        'problem_category':str,
        'problem_name': str,
        'problem_class': str,
        'problem_type': (type(None),str),
        'zone': (type(None),str),
        'scenario': str,
        'target': int,
        'date_create': str,
        'sla_reaction_deadline': (type(None),str),
        'sla_resolution_deadline': (type(None),str),
        'date_close': (type(None), str),
        'assigned_to': (type(None), int),
        'reject_comment': (type(None), str),
        'comment': (str,type(None)),
        "priority": (int,type(None)),
        "current_state": int,
        'history': list
    }
    for field, expected in type_map.items():
        if not isinstance(ticket.get(field), expected):
            raise CoreValidationBreak(f"{field} incorrect type")
    core_logger.info("party_ticket correct")
def full_ticket_validator(ticket: dict, config: dict)-> None:
    required_fields = list(config["ticket"]["TICKET"]["immutable"]) + list(config["ticket"]["TICKET"]["mutable"])
    if "comment" in ticket:
        required_fields.remove("comment")
    for field in required_fields:
        if field not in ticket:
            raise CoreValidationBreak(f"This {field} not in ticket")
    type_map= {
        "ticket_id": int,
        'creator_id': int,
        'creator_name': str,
        'branch_id': int,
        'branch_name': str,
        'event_type': str,
        'problem_category':str,
        'problem_name': str,
        'problem_class': str,
        'problem_type': (type(None),str),
        'zone': (type(None),str),
        'scenario': str,
        'target': str,
        'date_create': datetime,
        'sla_reaction_deadline': (type(None),datetime),
        'sla_resolution_deadline': (type(None),datetime),
        'date_close': (type(None), datetime),
        'assigned_to': (type(None), int, str),
        'reject_comment': (type(None), str),
        'comment': (str,type(None)),
        "priority": (str,type(None)),
        "current_state": str,
        'history': list
    }
    for field, expected in type_map.items():
        if not isinstance(ticket.get(field), expected):
            raise CoreValidationBreak(f"{field} incorrect type")
    if ticket["priority"] is not None and ticket["priority"] not in config['enum']['priority']:
        raise CoreValidationBreak(f"{ticket['priority']} incorrect value")
    if ticket["current_state"] not in config['enum']['TICKET_STATUS']:
        raise CoreValidationBreak(f"{ticket['current_state']} incorrect value")
    if ticket["sla_reaction_deadline"] is not None and ticket["sla_reaction_deadline"] < ticket["date_create"]:
        raise CoreValidationBreak("Reaction SLA before creation date")
    if ticket["sla_resolution_deadline"] is not None and ticket["sla_resolution_deadline"] < ticket["date_create"]:
        raise CoreValidationBreak("Resolution SLA before creation date")
    if ticket["sla_resolution_deadline"] < ticket["sla_reaction_deadline"]:
        raise CoreValidationBreak("Resolution SLA before reaction SLA date")
    if ticket['date_close']  and ticket["current_state"] not in ('CLOSED','CANCELLED'):
        raise LifecycleError(f"{ticket['date_close']} status not CLOSED or CANCELLED")
    if ticket['reject_comment'] and ticket["current_state"] != 'CANCELLED':
        raise LifecycleError(f"{ticket['reject_comment']} status not CANCELLED")
    if ticket['assigned_to'] and ticket["current_state"] in ('NEW','CONFIRMED'):
        raise LifecycleError(f"{ticket['assigned_to']} status {ticket['current_state']} incorrect ")
    if ticket["current_state"] in ("CLOSED", "CANCELLED") and not ticket["date_close"]:
        raise LifecycleError("Closed ticket without date_close")
    core_logger.info(f"ticket {ticket['ticket_id']} correct")

class User:
    __doc__ = "This class for user operations"

    def __init__(self,user: dict):
        self.id = user['user_id']
        self.name = user['user_name']
        self.api_id = user['api_user_id']
        self.role = user['role_name']
        self.depart_id = user.get('depart_id',None)
        self.depart_name = user.get('depart_name', None)
        self.branch_id = user.get('branch_id', None)
        self.branch_name = user.get('branch_name',None)

class Branch:
    __doc__ = "This class for branch operations"

    def __init__(self, branch:dict):
        self.branch_id = branch['branch_id']
        self.branch_name = branch['branch_name']
        self.branch_manager = branch.get('branch_manager',None)

class Ticket:
    __doc__ = "This class for ticket field validations and patch operations. He without hard logic"

    def __init__(self, data: dict):
        self.ticket_id = data.get('ticket_id',None)
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
        self.sla_reaction_deadline =  data.get('sla_reaction_deadline')
        self.sla_resolution_deadline = data.get('sla_resolution_deadline')
        self.date_close = data.get('date_close')
        self.assigned_to = data.get('assigned_to')
        self.reject_comment = data.get('reject_comment')
        self.comment = data.get('comment')
        self.priority = data.get('priority')
        self.current_state = data.get('current_state')
        self.history = []

    @staticmethod
    def _calculate_sla(event_data: dict, config: dict)-> dict:
        scen = event_data['scenario']
        type_sla = config['scenarios']['SCENARIOS'][scen]["sla_policy"]
        need_sla = config["SLA"]["SLA_POLICIES"][type_sla]
        react, resol = need_sla['reaction'], need_sla['resolution']

        def convert(value: str)-> Optional[timedelta]:
            if value is None:
                return None
            elif value.endswith("m"):
                return timedelta(minutes=int(value[:-1]))
            elif value.endswith("h"):
                return timedelta(hours=int(value[:-1]))
            elif value.endswith("d"):
                return timedelta(days=int(value[:-1]))
            raise ValueError(f"Invalid SLA format: {value}")

        res = {'reaction': convert(react),
               'resolution': convert(resol)}
        return res

    @classmethod
    def from_created(
            cls,
            event_data: dict,
            config: dict,
            user: Optional[User])-> Optional[Ticket]:
        now = datetime.now()
        sla_delta = cls._calculate_sla(event_data, config)
        date = {
        'creator_id': user.id,
        'creator_name': user.name,
        'branch_id': user.branch_id if user.branch_id else event_data.get('branch_id'),
        'branch_name': user.branch_name if user.branch_name else event_data.get('branch_name'),
        'event_type': event_data["event_type"],
        'problem_category': event_data['problem_category'],
        'problem_name': event_data['problem_name'],
        'problem_class': event_data['problem_class'],
        'problem_type': event_data['problem_type'],
        'zone': event_data["zone"],
        'scenario': event_data['scenario'],
        'target': event_data['target'],
        'date_create': now,
        'sla_reaction_deadline': None if sla_delta['reaction'] is None else now + sla_delta['reaction'],
        'sla_resolution_deadline': None if sla_delta['resolution'] is None else now + sla_delta['resolution'],
        'date_close': None,
        'assigned_to': None,
        'reject_comment': None,
        'comment': event_data.get('comment',None),
        "priority": event_data.get("priority", None),
        "current_state": event_data.get("current_state"),
        'history': []
        }

        return cls(date)
    @classmethod
    def from_data_base(cls,
                       ticket:dict):
        return cls(ticket)

    @staticmethod
    def for_data_base(ticket, config:dict)->dict:
        priority_map = config['enum']['priority']
        state_map = config['enum']['TICKET_STATUS']
        depart_map = config['enum']['DEPARTMENTS']

        res = {'ticket_id': getattr(ticket,'ticket_id',None),
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
                  'sla_reaction_deadline': ticket.sla_reaction_deadline.strftime("%Y-%m-%d %H:%M:%S") if ticket.sla_reaction_deadline else None,
                  'sla_resolution_deadline': ticket.sla_resolution_deadline.strftime("%Y-%m-%d %H:%M:%S") if ticket.sla_resolution_deadline else None,
                  'current_state': state_map.get(ticket.current_state),
                  'date_close': ticket.date_close.strftime("%Y-%m-%d %H:%M:%S") if ticket.date_close else None,
                  'assigned_to': ticket.assigned_to,
                  'reject_comment': ticket.reject_comment,
                  'comment': ticket.comment,
                  'priority': priority_map.get(ticket.priority)}
        return res

    def update_solution(self, solution:dict)-> Optional[Ticket]:
        self.current_state = solution['current_state']
        self.target = solution.get('target', self.target)
        self.assigned_to = solution.get('assigned_to', None)
        return self

    def _validation_ticket(self,config):
        if self.priority is not None and self.priority not in config['enum']['priority']:
            raise CoreValidationBreak(f"{self.priority} incorrect value")
        if self.current_state not in config['enum']['TICKET_STATUS']:
            raise CoreValidationBreak(f"{self.current_state} incorrect value")
        if self.sla_reaction_deadline is not None and self.sla_reaction_deadline < self.date_create:
            raise CoreValidationBreak("Reaction SLA before creation date")
        if self.sla_resolution_deadline is not None and self.sla_resolution_deadline < self.date_create:
            raise CoreValidationBreak("Resolution SLA before creation date")
        if self.sla_resolution_deadline < self.sla_reaction_deadline:
            raise CoreValidationBreak("Resolution SLA before reaction SLA date")
        if self.date_close and self.current_state not in ('CLOSED', 'CANCELLED'):
            raise LifecycleError(f"{self.date_close} status not CLOSED or CANCELLED")
        if self.reject_comment and self.current_state != 'CANCELLED':
            raise LifecycleError(f"{self.reject_comment} status not CANCELLED")
        if self.assigned_to and self.current_state in ('NEW', 'CONFIRMED'):
            raise LifecycleError(f"{self.assigned_to} status {self.current_state} incorrect ")
        if self.current_state in ("CLOSED", "CANCELLED") and not self.date_close:
            raise LifecycleError("Closed ticket without date_close")

    def _validation_patch(self, patch:dict,config:dict, user: Optional[User],type_fsm:dict):
        if self.event_type == "ALERT":
            raise CoreValidationBreak("ALERT not mutable type")

        actual_state = patch.get('current_state',self.current_state)
        if 'current_state' in patch:
            if patch['current_state'] not in type_fsm:
                raise CoreValidationBreak(f"{patch['current_state']} incorrect type")

            next_states = type_fsm[self.current_state]['next'] or []
            if patch['current_state'] not in next_states:
                raise LifecycleError("Invalid lifecycle transition")

        if actual_state in ("CLOSED", "CANCELLED") and "date_close" not in patch:
            raise LifecycleError("Closing ticket requires date_close")

        if 'date_close' in patch:
            if not isinstance(patch['date_close'], datetime):
                raise CoreValidationBreak(f" This {patch['date_close']} incorrect type")
            if actual_state not in ('CLOSED', 'CANCELLED'):
                raise LifecycleError(f" This {patch['date_close']} incorrect on step {actual_state}")

        if 'assigned_to' in patch:
            if not isinstance(patch['assigned_to'], int):
                raise CoreValidationBreak(f" This {patch['assigned_to']} incorrect type")
            if actual_state != 'IN_PROGRESS':
                raise LifecycleError(f" This {patch['assigned_to']} incorrect on step {actual_state}")
            if self.assigned_to:
                raise CoreValidationBreak(f"Ticket assigned another changed")

        if 'priority' in patch:
            if not isinstance(patch['priority'], str):
                raise CoreValidationBreak(f" This {patch['priority']} incorrect type")
            if actual_state != 'CONFIRMED' and not config['roles']["ROLES"][user.role]['permissions'][
                'extra_change_priority']:
                raise LifecycleError(f" This {patch['priority']} incorrect on step {actual_state}")

        if 'comment' in patch:
            if patch['comment'] and not isinstance(patch['comment'], (str, type(None))):
                raise CoreValidationBreak(f" This {patch['comment']} incorrect type")

        if actual_state == "CANCELLED" and "reject_comment" not in patch:
            raise CoreValidationBreak("Cancel requires reject_comment")

        if 'reject_comment' in patch:
            if not isinstance(patch['reject_comment'], str):
                raise CoreValidationBreak(f" This {patch['reject_comment']} incorrect type")
            if actual_state != 'CANCELLED':
                raise LifecycleError(f" This {patch['reject_comment']} incorrect on step {actual_state}")
        core_logger.info(f"ticket {self.ticket_id} and patch correct")

    def _apply_patch(self, patch: dict):
        allowed_fields = {'current_state','date_close','assigned_to',
                 'priority','comment','reject_comment'}
        for field, value in patch.items():
            if field in allowed_fields:
                old = getattr(self,field)
                if old != value:
                    setattr(self,field, value)
                    self._log_history(field,old,value)

    def _log_history(self, field, old, new):
        self.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "changes": field,
             "old": old,
             "new": new})

    def update_ticket(self, config:dict, patch:dict, user:Optional[User],type_fsm:dict):
        try:
            self._validation_patch(patch,config,user,type_fsm)
            self._apply_patch(patch, user)
            self._validation_ticket(config)
        except CoreValidationBreak:
            raise
        except LifecycleError:
            raise
        core_logger.info(f"Ticket {self.ticket_id} update patch {patch.keys()}")
        return self

def has_permission(role_name:str, flag: str, config: dict)->bool:
    permission = config["roles"]["ROLES"][role_name]['permissions']
    return permission.get(flag, False)
