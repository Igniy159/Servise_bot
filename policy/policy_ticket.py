"""
Validating input ticket data from a business logic perspective
Checking object relationships for consistency with business logic
"""
from api.command import CmdCreateTicket
from core.exceptions import CoreValidationBreak, PermissionDenied
from core.ticket_core import User,Ticket
from datetime import datetime

class Policy:
    """
    Base class for command policies.
    Handles config-based validation and user access control for specific functionality.
    """
    def __init__(self, user: User, config:dict, cmd):
        self.user = user
        self.cmd = cmd
        self.config = config
        self.enum = config['enum']
        self.access = config['roles']['ROLES'][user.role]['permissions']['lead_ticket']

    def _access_user(self, action: str):
        if not self.access[action]:
            raise PermissionDenied(f" User {self.user.name} cannot access {action} ticket")

class PolicyCreateTicket(Policy):
    """
    Validates ticket creation requests.
    Coordinates config checks through child policies and determines the routing context
    """
    def _check_branch_id(self):
        if self.user.branch_id is None and self.cmd.branch_id is None:
            raise CoreValidationBreak("if changed not branch: in command need field branch_id")

    def _check_priority(self):
        if self.cmd.priority not in self.enum['priority']:
            raise CoreValidationBreak(f"INCORRECT priority- {self.cmd.priority}")

    def validate_cmd(self):
        """Checks the command for compliance with the config"""
        raise NotImplementedError('Must be implemented in subclass')
    def resolve_decision(self):
        """Solution containing the required fields to create a request (scenario/target/priority)"""
        raise NotImplementedError('Must be implemented in subclass')

    def policy_cmd(self):
        """ Consistently calls the access check for creating a request,
         and checks the command for compliance with the config.
         Returns a solution containing the required fields to create a request"""
        self._access_user('create')
        self._check_branch_id()
        self._check_priority()
        self.validate_cmd()
        return self.resolve_decision()

class PolicyObject(PolicyCreateTicket):
    """Checks the creation command for the object type."""
    def __init__(self, user: User, cmd: CmdCreateTicket, config: dict):
        super().__init__(user,config, cmd)
        self.object = config['object']['ARS_OBJECT']
        self.matrix = config["priority_matrix"]['OBJECT_CLASSES']

    def validate_cmd(self):
        if self.cmd.problem_category not in self.enum["zones"]:
            raise CoreValidationBreak(f"INCORRECT type_problem - {self.cmd.problem_category}")
        if self.cmd.problem_name not in self.object[self.cmd.zone]:
            raise CoreValidationBreak(f"INCORRECT problem - {self.cmd.problem_name}")
        if self.cmd.problem_class not in self.enum['OBJECT_CLASSES']:
            raise CoreValidationBreak(f"INCORRECT OBJECT_CLASS - {self.cmd.problem_class}")
        if self.cmd.problem_type not in self.enum["PROBLEMS"]:
            raise CoreValidationBreak(f"INCORRECT type_problem - {self.cmd.problem_type}")
        if  self.cmd.zone is None or self.cmd.zone not in self.enum["zones"]:
            raise CoreValidationBreak("Incorrect zone")

    def resolve_decision(self) -> dict:
        resolve = {'scenario': None,
                   'target': None,
                   'priority': None}
        matrix = self.matrix[self.cmd.problem_class][self.cmd.problem_type]
        resolve['priority'] = self.cmd.priority or matrix['priority']
        resolve['scenario'] = matrix["scenario"]
        resolve['target'] = self.object[self.cmd.zone][self.cmd.problem_name]['target']
        resolve['target_id'] = self.enum['DEPARTMENTS'][resolve['target']]
        return resolve

class PolicyRequest(PolicyCreateTicket):
    """Checks the creation command for the request type."""
    def __init__(self, user: User, cmd: CmdCreateTicket, config: dict):
        super().__init__(user, config, cmd)
        self.request = config['request']
        self.rules_req = config["rules_request"]['REQUEST_CLASSES']

    def validate_cmd(self):
        if self.cmd.problem_category not in self.enum["REQUEST_CATEGORY"]:
            raise CoreValidationBreak(f"INCORRECT request_category {self.cmd.problem_category}")
        if self.cmd.problem_name not in self.request[self.cmd.problem_category]:
            raise CoreValidationBreak(f"INCORRECT request - {self.cmd.problem_name}")
        if self.cmd.problem_class not in self.enum['REQUEST_CLASSES']:
            raise CoreValidationBreak(f"INCORRECT request_class - {self.cmd.problem_class}")
        if self.cmd.problem_type not in self.enum['TYPE_REQUEST']:
            raise CoreValidationBreak(f"INCORRECT request_type - {self.cmd.problem_type}")
        if self.cmd.zone is not None and self.cmd.zone not in self.enum["zones"]:
            raise CoreValidationBreak("Incorrect zone")

    def resolve_decision(self) -> dict:
        req = self.rules_req[self.cmd.problem_class]
        resolve = {'priority': self.cmd.priority or req[self.cmd.problem_type]['priority'],
                   'scenario': req[self.cmd.problem_type]['scenario'],
                   'target': req['target']}
        return resolve

class PolicyAlert(PolicyCreateTicket):
    """Checks the creation command for the alert type."""
    def __init__(self, user: User, cmd: CmdCreateTicket, config: dict):
        super().__init__(user, config, cmd)
        self.alert = config['alerts']
        self.rules_alert = config['rules_alert']

    def validate_cmd(self):
        if self.cmd.problem_category not in self.enum['CATEGORY_ALERTS']:
            raise CoreValidationBreak(f"INCORRECT alert_category - {self.cmd.problem_category}")
        if self.cmd.problem_name not in self.alert[self.cmd.problem_category]:
            raise CoreValidationBreak(f"INCORRECT alert_problem - {self.cmd.problem_name}")
        if self.cmd.problem_class not in self.enum['CLASS_ALERTS']:
            raise CoreValidationBreak(f"INCORRECT alert_class - {self.cmd.problem_class}")
        if self.cmd.problem_type is not None:
            raise CoreValidationBreak("ALERT must not contain problem_type")
        if self.cmd.zone is not None and self.cmd.zone not in self.enum["zones"]:
            raise CoreValidationBreak("Incorrect zone")

    def resolve_decision(self) -> dict:
        resolve = {'scenario': None,
                   'target': None,
                   'priority': None}
        al = self.rules_alert[self.cmd.problem_class]
        resolve['scenario'] = al['scenario']
        resolve["target"] = al["target"]
        return resolve


class Actions:
    def __init__(self, cmd):
        self.cmd = cmd
class ConfirmAction(Actions):
    pass
class RejectAction(Actions):
    def __init__(self, cmd):
        cmd.date_close = datetime.now()
        super().__init__(cmd)
class PriorityAction(Actions):
    pass
class AssignAction(Actions):
    pass
class OnWaitAction(Actions):
    pass
class OffWaitAction(Actions):
    pass
class FinishAction(Actions):
    pass
class CloseAction(Actions):
    def __init__(self, cmd):
        cmd.date_close = datetime.now()
        super().__init__(cmd)

class PolicyApplyTicket(Policy):
    def __init__(self, ticket: Ticket, user: User, config: dict, cmd):
        super().__init__(user, config, cmd)
        self.ticket = ticket
        self._check_branch()
        self._not_alert()

    def _not_alert(self):
        if self.ticket.event_type == "ALERT":
            raise CoreValidationBreak("ALERT not mutable type")

    def _check_branch(self):
        if self.user.branch_name is not None and self.user.branch_name != self.ticket.branch_name:
            raise PermissionDenied(" User action only mine branch_ticket")

    def access_user(self):
        """checking user access through heirs"""
        raise NotImplementedError('Must be implemented in subclass')
    def resolve_patch(self):
        """generate patch for update ticket"""
        raise NotImplementedError('Must be implemented in subclass')

class PolicyConfirm(PolicyApplyTicket):
    def access_user(self):
        self._access_user("confirm")

    def resolve_patch(self):
        return ConfirmAction(self.cmd)

class PolicyReject(PolicyApplyTicket):
    def access_user(self):
        self._access_user("reject")
        self._spec_access()

    def resolve_patch(self):
        return RejectAction(self.cmd)

    def _spec_access(self):
        if self.user.role != 'OWNER':
            if self.ticket.current_state not in ('NEW','CONFIRMED'):
                raise PermissionDenied("You can cancel a new application or with admin access.")

class PolicyPriority(PolicyApplyTicket):
    def access_user(self):
        self._access_user("priority")
    def resolve_patch(self):
        return PriorityAction(self.cmd)

class PolicyAssign(PolicyApplyTicket):
    def access_user(self):
        self._access_user("assign")
        self._race_condition()
    def resolve_patch(self):
        self.cmd.assigned_to = self.user.id
        return AssignAction(self.cmd)
    def _race_condition(self):
        if self.ticket.assigned_to:
            raise PermissionDenied("Ticket has already been accepted for processing")
class PolicyOnWait(PolicyApplyTicket):
    def access_user(self):
        self._access_user("on_waiting")
    def resolve_patch(self):
        return OnWaitAction(self.cmd)

class PolicyOffWait(PolicyApplyTicket):
    def access_user(self):
        self._access_user("off_waiting")
    def resolve_patch(self):
        return OffWaitAction(self.cmd)
class PolicyFinish(PolicyApplyTicket):
    def access_user(self):
        self._access_user("finish")

    def resolve_patch(self):
        return FinishAction(self.cmd)
class PolicyClose(PolicyApplyTicket):
    def access_user(self):
        self._access_user("close")
    def resolve_patch(self):
        return CloseAction(self.cmd)

class PolicyGet(Policy):
    def role_filter(self):
        if self.user.role == "MANAGER":
            self.cmd.branch_id = self.user.branch_id
        if self.user.role == "SPECIALIST":
            self.cmd.depart_id = self.user.depart_id
        if self.user.role == "EMPLOYEE":
            self.cmd.creator_id = self.user.id
        return self.cmd


class PolicyGetTicket(PolicyGet):
    def access_user(self):
        self._access_user('get_ticket')

class PolicyGetHistory(PolicyGet):
    def access_user(self):
        self._access_user('get_history')
