from api.command import CmdCreateAlert, QueryGetAlerts
from core.ticket_core import User, Alert, RuleAlert
from policy.policy_alert import PolicyAlert
from repository.unit_of_work import UoW
from service.recipients import RecipientResolver

class AlertService:
    def __init__(self,
                 raw_config: dict,
                 uow:UoW):
        self.uow = uow
        self.control = PolicyAlert(raw_config['roles'])

    def create(self, cmd: CmdCreateAlert, actor: User):
        self.control.access_user(actor,'create_ticket')
        rule = self.uow.alerts.get_rules({'code_alert': cmd.code_alert})
        alert = Alert(actor_id=actor.id,
                      branch_id=actor.branch_id,
                      code_alert=CmdCreateAlert.code_alert,
                      comment=cmd.comment)
        self.uow.alerts.create(alert)
        view_alert = AlertView(alert, rule, actor.branch_name)
        recipient = RecipientResolver.get_alert_recipients(self.uow, actor,rule)
        return view_alert,recipient



    def get(self, cmd: QueryGetAlerts, actor:User):
        self.control.access_user(actor, 'get_ticket')
        alerts = self.uow.alerts.get({cmd.dict()})
        return alerts

class AlertView:
    def __init__(self,
                 alert: Alert,
                 rule: RuleAlert,
                 branch_name: str):
        self.alert = alert
        self.rule = rule
        self.branch_name = branch_name
    def __str__(self):
        return f"""{self.rule.name_alert}\n{self.alert.comment}
                {self.branch_name}\n{self.alert.date_create}"""
