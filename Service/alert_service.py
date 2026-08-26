from core.schemas import CmdCreateAlert, QueryGetAlerts
from core.exceptions import ServiseValidationBreak
from core.ticket_core import User, Alert, Rule, Permission
from repository.unit_of_work import UoW
from service.recipients import RecipientResolver, Recipients


class AlertService:
    def __init__(self,
                 control: Permission,
                 uow:UoW):
        self.uow = uow
        self.control = control

    def create(self, cmd: CmdCreateAlert, actor: User)-> tuple[AlertView, Recipients]:
        self.control.can(actor,'lead_ticket','create')
        rule = self.uow.rule.get_rules({'code': cmd.code_alert})
        if not rule:
            raise ServiseValidationBreak('Not found rule')
        rule = rule[0]
        alert = Alert(actor_id=actor.id,
                      branch_id=actor.branch_id,
                      code_alert=cmd.code_alert,
                      comment=cmd.comment)
        self.uow.alerts.create(alert)
        view_alert = AlertView(alert, rule, actor.branch_name)
        recipient = RecipientResolver.get_create_recipients(self.uow, actor, rule)
        return view_alert,recipient

    def get(self, cmd: QueryGetAlerts, actor:User)-> list[Alert]:
        self.control.can(actor, 'lead_ticket','get_ticket')
        alerts = self.uow.alerts.get(cmd.dict())
        return alerts

class AlertView:
    def __init__(self,
                 alert: Alert,
                 rule: Rule,
                 branch_name: str):
        self.alert = alert
        self.rule = rule
        self.branch_name = branch_name
