from datetime import datetime, timedelta
from core.exceptions import CoreValidationBreak
from core.ticket_core import Ticket, User, State
from policy.policy_ticket import (PolicyObject, PolicyRequest,
                                  PolicyAlert, PolicyConfirm,
                                  PolicyReject, PolicyPriority,
                                PolicyOnWait, PolicyOffWait,
                                  PolicyFinish, PolicyClose,
                                  PolicyAssign, PolicyGetHistory, PolicyGetTicket)
from repository.unit_of_work import UoW
from api.command import (CmdCreateTicket, CmdCloseTicket, CmdAssignTicket, CmdFinishTicket,
                         CmdRejectTicket, CmdPriorityTicket, CmdConfirmTicket, CmdOnWaitingTicket,
                         CmdOffWaitingTicket, QueryGetTicket, QueryGetHistoryTicket)
from service.event_builder import EventCreateTicket, EventApplyTicket, EventGetTicket, EventGetHistory
from service.recipients import RecipientsCreateTicket, RecipientsApplyTicket, Recipient

class TicketService:
    def __init__(self, config:dict, uow: UoW):
        self.uow = uow
        self.config = config

    def write(self,
              user:User,
              cmd:CmdCreateTicket
              ) -> tuple[EventCreateTicket,RecipientsCreateTicket]:
        #Определяем тип события
        type_event = self._type_resolver(self.config['enum'],cmd)
        if type_event == "OBJECT_PROBLEM":
            control = PolicyObject(user, cmd, self.config)
        elif type_event == "REQUEST":
            control = PolicyRequest(user, cmd, self.config)
        else:
            control = PolicyAlert(user, cmd, self.config)
        #Валидируем команду и принимаем решение (сценарий, отдел, приоритет)
        resolve = control.policy_cmd()
        if cmd.branch_id:
            resolve['branch_name'] = self.uow.branches.get({'branch_id': cmd.branch_id}
            )[0]['branch_name']
        resolve = self.calculate_sla(resolve, self.config['scenarios'], self.config['SLA'])
        #Собираем контекст из БД
        manager = self.uow.users.get({'user_activity': 1,
                                       'role_id': 2,
                                       'branch_id': user.branch_id})
        owner = self.uow.users.get({'user_activity': 1,
                                     'role_id': 4})
        depart = self.uow.users.get({'user_activity': 1,
                                      'role_id': 3,
                                      'depart_id': resolve['target_id']})
        context = {'manager': manager,
                   'owner': owner,
                   'depart': depart}
        #Собираем из контекста правила эскалации(отдел, текущий статус, получателей)
        solution, recipient = self.escalation(self.config['scenarios'], cmd, context)
        #Создаём тикет
        ticket = Ticket.from_created(cmd, resolve, user)
        ticket.validate_sla()
        ticket.update_solution(solution)
        state_for_history = ticket.current_state
        ticket_for_db = Ticket.for_data_base(ticket, self.config['enum'])
        #Записываем тикет и историю в БД
        ticket_id = self.uow.tickets.create(ticket_for_db)
        self.uow.tickets.insert_history(ticket_id,
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  user.id,
                                  'current_state',
                                  None,
                                  state_for_history)
        #Формируем событие и ответ для API
        event_alert = EventCreateTicket(user,ticket)
        recipient = RecipientsCreateTicket(user,recipient)
        return event_alert, recipient

    @staticmethod
    def _type_resolver(enums:dict, cmd:CmdCreateTicket) -> str:
        """The function determines the event type through the config and returns it as a string"""
        type_event = ""
        if cmd.problem_category in enums['zones']:
            type_event = 'OBJECT_PROBLEM'
        elif cmd.problem_category in enums['REQUEST_CATEGORY']:
            type_event = 'REQUEST'
        elif cmd.problem_category in enums['CATEGORY_ALERTS']:
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
                   context: dict) -> tuple[dict,dict]:
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

    def patch(self,
              user:User,
              cmd
              ) -> tuple[EventApplyTicket,RecipientsApplyTicket]:
        fsm = self.config['ticket_lifecycle']['LIFECYCLE']
        # из БД поднимаем заявку для изменения
        ticket = self.uow.tickets.get({"ticket_id": cmd.ticket_id})
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
        policy = cmd_policy_map.get(type(cmd))
        control = policy(ticket, user, self.config, cmd)
        control.access_user()
        action = control.resolve_patch()
        #переписываем тикет
        updated_ticket = ticket.update_ticket(fsm, action)
        #записываем в БД
        self.uow.tickets.update(updated_ticket)
        for record in updated_ticket.history:
            self.uow.tickets.insert_history(updated_ticket.ticket_id,
                                  record['timestamp'],
                                  user.id,
                                  record['changes'],
                                  record['old'],
                                  record['new'])
        ticket.history.clear()
        #Собираем контекст из БД
        manager = self.uow.users.get({'user_activity': 1,
                                       'role_id': 2,
                                       'branch_id': ticket.branch_id})
        target_id = self.config['enum'][ticket.target]
        depart = self.uow.users.get({'user_activity': 1,
                                      'role_id': 3,
                                      'depart_id': target_id})
        context = {'manager': manager,
                   'depart': depart}
        event_alert = EventApplyTicket(user,ticket,action)
        recipient = RecipientsApplyTicket(user,action,context)
        return  event_alert, recipient


    def get(self,
                    user:User,
                    cmd:QueryGetTicket
                    )-> tuple[EventGetTicket,Recipient]:
        control = PolicyGetTicket(user,self.config,cmd)
        control.access_user()
        modified_cmd = control.role_filter()
        tickets = self.uow.tickets.get(modified_cmd)
        res = []
        if tickets:
            for ticket in tickets:
                if cmd.size == 'full':
                    res.append(self._full_view(ticket, user.role, self.config['ticket_masks']))
                else:
                    res.append(self._short_view(ticket,self.config['ticket_masks']))
        event_alert = EventGetTicket(user,res)
        recipient = Recipient(user)
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

    def history(self,
                    user:User,
                    cmd:QueryGetHistoryTicket
                    )->tuple[EventGetHistory,Recipient]:
        control = PolicyGetHistory(user,self.config,cmd)
        control.access_user()
        modified_cmd = control.role_filter()
        history = self.uow.tickets.get_history(modified_cmd)
        event_alert = EventGetHistory(user,history)
        recipient = Recipient(user)
        return event_alert, recipient
