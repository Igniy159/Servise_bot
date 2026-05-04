from service.common import transactional
from core.ticket_core import User,State
from core.exceptions import PermissionDenied, CoreValidationBreak, IncorrectWrite
from core.ticket_core import Ticket
from policy.policy_ticket import PolicyObject, PolicyRequest, PolicyAlert, PolicyConfirm, PolicyReject, PolicyPriority, \
    PolicyOnWait, PolicyOffWait, PolicyFinish, PolicyClose, PolicyAssign, PolicyGetHistory, PolicyGetTicket
from logger.logger import core_logger
from repository.write_model import ticket_assert, insert_history_record, ticket_update
from repository.read_model import get_users_with_data, get_tickets_with_data, fetch_history_ticket, get_branch_with_data
from api.command import (CmdCreateTicket, CmdCloseTicket, CmdAssignTicket, CmdFinishTicket,
                         CmdRejectTicket, CmdPriorityTicket, CmdConfirmTicket, CmdOnWaitingTicket,
                         CmdOffWaitingTicket, QueryGetTicket, QueryGetHistoryTicket)
from datetime import datetime, timedelta

from service.event_builder import EventCreateTicket, EventApplyTicket, EventGetTicket, EventGetHistory
from service.recipients import RecipientsCreateTicket, RecipientsApplyTicket, Recipient

class CreatorTicket:
    def __init__(self,user:User,cmd: CmdCreateTicket,config:dict,con):
        self.user = user
        self.cmd = cmd
        self.config = config
        self.con = con

    @transactional
    def write_ticket(self) -> tuple:
        #Определяем тип события
        type_event = self._type_resolver()
        if type_event == "OBJECT_PROBLEM":
            control = PolicyObject(self.user, self.cmd, self.config)
        elif type_event == "REQUEST":
            control = PolicyRequest(self.user, self.cmd, self.config)
        else:
            control = PolicyAlert(self.user, self.cmd, self.config)
        #Валидируем команду и принимаем решение (сценарий, отдел, приоритет)
        try:
            resolve = control.policy_cmd()
        except CoreValidationBreak as e:
            core_logger.error(f"Event {self.cmd['problem_name']} incorrect. {e}")
            raise
        except PermissionDenied as e:
            core_logger.error(f"Error in access user: {e}")
            raise
        if self.cmd.branch_id:
            resolve['branch_name'] = get_branch_with_data(
                {'branch_id': self.cmd.branch_id}, self.con
            )[0]['branch_name']
        resolve = self.calculate_sla(resolve, self.config['scenarios'], self.config['SLA'])
        #Собираем контекст из БД
        manager = get_users_with_data({'user_activity': 1,
                                       'role_id': 2,
                                       'branch_id': self.user.branch_id},
                                      self.con)
        owner = get_users_with_data({'user_activity': 1,
                                     'role_id': 4},
                                    self.con)
        depart = get_users_with_data({'user_activity': 1,
                                      'role_id': 3,
                                      'depart_id': resolve['target_id']})
        context = {'manager': manager,
                   'owner': owner,
                   'depart': depart}
        #Собираем из контекста правила эскалации(отдел, текущий статус, получателей)
        solution, recipient = self.escalation(self.config['scenarios'], self.cmd, context)
        #Создаём тикет
        ticket = Ticket.from_created(self.cmd, resolve, self.user)
        ticket.validate_sla()
        ticket.update_solution(solution)
        state_for_history = ticket.current_state
        ticket_for_db = Ticket.for_data_base(ticket, self.config['enum'])
        #Записываем тикет и историю в БД
        try:
            ticket_id = ticket_assert(ticket_for_db,self.con)
        except IncorrectWrite as e:
            core_logger.error(f"Ticket has not write. Reason: {e}")
            raise
        try:
            insert_history_record(ticket_id,
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  self.user.id,
                                  'current_state',
                                  None,
                                  state_for_history, con=self.con)
        except IncorrectWrite as e:
            core_logger.error(f"History has not write. Reason: {e}")
            raise
        #Формируем событие и ответ для API
        event_alert = EventCreateTicket(self.user,ticket)
        recipient = RecipientsCreateTicket(self.user,recipient)
        return event_alert, recipient


    def _type_resolver(self) -> str:
        """The function determines the event type through the config and returns it as a string"""
        enums = self.config['enum']
        type_event = ""
        if self.cmd.problem_category in enums['zones']:
            type_event = 'OBJECT_PROBLEM'
        elif self.cmd.problem_category in enums['REQUEST_CATEGORY']:
            type_event = 'REQUEST'
        elif self.cmd.problem_category in enums['CATEGORY_ALERTS']:
            type_event = 'ALERT'
        return type_event

    @staticmethod
    def calculate_sla(resolve: dict, scenario: dict, sla_metrix: dict) -> dict:
        scen = resolve['scenario']
        type_sla = scenario['SCENARIOS'][scen]["sla_policy"]
        need_sla = sla_metrix["SLA_POLICIES"][type_sla]
        react_time, resol_time = need_sla['reaction'], need_sla['resolution']

        def _convert(value: str)-> datetime | None:
            now = datetime.now()
            if value is None:
                return None
            if value.endswith("m"):
                return timedelta(minutes=int(value[:-1])) + now
            if value.endswith("h"):
                return timedelta(hours=int(value[:-1])) + now
            if value.endswith("d"):
                return timedelta(days=int(value[:-1])) + now
            raise ValueError(f"Invalid SLA format: {value}")

        resolve['react_time'] = _convert(react_time)
        resolve['resol_time'] = _convert(resol_time)
        return resolve

    @staticmethod
    def escalation(scenarios: dict,
                   cmd: CmdCreateTicket,
                   context: dict) -> tuple:
        need_confirm = scenarios['SCENARIOS'][cmd['scenario']]["confirmation_required"]
        solution = {}
        recipient = {}

        if not context['depart'] and not context['manager']:
            solution['assigned_to'] = context['owner'][0]['user_id']
            solution['target'] = 'TOP_MANAGEMENT'
            solution['current_state'] = State.IN_PROGRESS
            recipient['target'] = context['owner'][0]['api_user_id']

        elif not context['depart'] and context['manager'] and need_confirm:
            solution['target'] = 'TOP_MANAGEMENT'
            solution['current_state'] = State.NEW
            recipient['manager'] = context['manager'][0]['api_user_id']

        elif not context['depart'] and context['manager'] and not need_confirm:
            solution['target'] = 'TOP_MANAGEMENT'
            solution['current_state'] = State.CONFIRMED
            recipient['manager'] = context['manager'][0]['api_user_id']
            recipient['target'] = [users['api_user_id'] for users in context['depart']]

        elif not context['manager'] and context['depart']:
            solution['current_state'] = State.CONFIRMED
            recipient['target'] = [users['api_user_id'] for users in context['depart']]

        elif context['manager'] and context['depart']:
            solution['current_state'] = State.NEW
            recipient['manager'] = context['manager'][0]['api_user_id']

        return solution, recipient

class UpdaterTicket:
    def __init__(self,user:User, cmd, config:dict, con):
        self.user = user
        self.cmd = cmd
        self.config = config
        self.con = con


    @transactional
    def apply_write_patch(self) -> tuple:
        fsm = self.config['ticket_lifecycle']['LIFECYCLE']
        # из БД поднимаем заявку для изменения
        ticket = get_tickets_with_data({"ticket_id": self.cmd.ticket_id}, self.con)
        if ticket:
            ticket = Ticket(ticket[0])
        else:
            raise CoreValidationBreak("Ticket not found")
        #маппер для вызова нужного класса, в зависимости от типа команды
        cmd_policy_map = {
            CmdRejectTicket: PolicyReject,
            CmdConfirmTicket: PolicyConfirm,
            CmdPriorityTicket: PolicyPriority,
            CmdAssignTicket: PolicyAssign,
            CmdOnWaitingTicket: PolicyOnWait,
            CmdOffWaitingTicket: PolicyOffWait,
            CmdFinishTicket: PolicyFinish,
            CmdCloseTicket: PolicyClose
        }
        #определяем команду и создаём патч
        policy = cmd_policy_map.get(type(self.cmd))
        control = policy(ticket, self.user, self.config, self.cmd)
        control.access_user()
        action = control.resolve_patch()
        #переписываем тикет
        updated_ticket = ticket.update_ticket(fsm, action)
        #записываем в БД
        ticket_update(updated_ticket, self.con)
        for record in updated_ticket.history:
            insert_history_record(updated_ticket.ticket_id,
                                  record['timestamp'],
                                  self.user.id,
                                  record['changes'],
                                  record['old'],
                                  record['new'],
                                  self.con)
        ticket.history.clear()

        #Собираем контекст из БД
        manager = get_users_with_data({'user_activity': 1,
                                       'role_id': 2,
                                       'branch_id': ticket.branch_id},
                                      self.con)
        target_id = self.config['enum'][ticket.target]
        depart = get_users_with_data({'user_activity': 1,
                                      'role_id': 3,
                                      'depart_id': target_id})
        context = {'manager': manager,
                   'depart': depart}
        event_alert = EventApplyTicket(self.user,ticket,action)
        recipient = RecipientsApplyTicket(self.user,action,context)
        return  event_alert, recipient

class GetterTicket:
    def __init__(self,user:User, cmd:QueryGetTicket, config:dict,con):
        self.user = user
        self.cmd = cmd
        self.config = config
        self.con = con

    @transactional
    def receive_tickets(self) -> tuple:
        control = PolicyGetTicket(self.user,self.config,self.cmd)
        control.access_user()
        modified_cmd = control.role_filter
        tickets = get_tickets_with_data(modified_cmd, self.con)
        res = []
        if tickets:
            for ticket in tickets:
                if self.cmd.size == 'full':
                    res.append(self._full_view(ticket, self.user.role, self.config['ticket_masks']))
                else:
                    res.append(self._short_view(ticket,self.config['ticket_masks']))
        event_alert = EventGetTicket(res)
        recipient = Recipient(self.user)
        return event_alert, recipient

    @staticmethod
    def _full_view(ticket: dict, role: str, masks:dict)->dict:
        ticket_view = {}
        need_field = masks['FULL_VIEW'][role]
        for key, val in ticket.items():
            if key in need_field:
                ticket_view[key] = val
        return ticket_view

    @staticmethod
    def _short_view(ticket: dict, masks: dict)->dict:
        need_field = masks['SHORT_VIEW']
        ticket_view = {}
        for key, val in ticket.items():
            if key in need_field:
                ticket_view[key] = val
        return ticket_view



@transactional
def receive_history(user: User,
                    cmd: QueryGetHistoryTicket,
                    config:dict,
                    con)->tuple:
    control = PolicyGetHistory(user,config,cmd)
    control.access_user()
    modified_cmd = control.role_filter
    history = fetch_history_ticket(modified_cmd, con=con)
    event_alert = EventGetHistory(history)
    recipient = Recipient(user)
    return event_alert, recipient
