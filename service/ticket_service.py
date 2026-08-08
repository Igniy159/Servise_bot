from datetime import datetime
from core.enums import Role, DATE_FORMAT
from core.exceptions import CoreValidationBreak
from core.ticket_core import Ticket, User, State, Permission, TicketContext, TicketLifecycle, TicketView
from repository.unit_of_work import UoW
from core.schemas import CmdCreateTicket,QueryGetTicket, QueryGetHistoryTicket, CmdChangeState
from service.recipients import RecipientResolver, Recipients
from service.user_service import PolicyUser


class TicketService:
    def __init__(self, control: Permission, uow: UoW):
        self.uow = uow
        self.control = control

    def create(self,
              actor:User,
              cmd:CmdCreateTicket)->tuple[TicketView,Recipients]:
        self.control.can(actor,'lead_ticket','create')
        rules_ticket = self.uow.rule.get_rules({'code': cmd.code_rule})
        if not rules_ticket:
            raise CoreValidationBreak(f'Incorrect rule_ticket {cmd.code_rule}')
        rule = rules_ticket[0]

        recipients = RecipientResolver.get_create_recipients(uow=self.uow,
                                                            actor=actor,
                                                            rule=rule)
        state = self._resolve_state(recipients,actor)
        context = TicketContext(actor.id,
                                actor.branch_id,
                                cmd.comment,
                                cmd.severity,
                                cmd.file_id)
        ticket = Ticket(code_ticket=rule.code,
                        state=state,
                        context=context,
                        date_create=datetime.now().strftime(DATE_FORMAT))
        ticket_id =  self.uow.tickets.create(ticket)
        ticket.id = ticket_id

        self.uow.tickets.insert_history(ticket_id,
                                  datetime.now().strftime(DATE_FORMAT),
                                  actor.id,
                                  'current_state',
                                  None,
                                  ticket.state.name)
        view = TicketView(ticket, rule.name, actor.branch_name)
        return view, recipients

    @staticmethod
    def _resolve_state(recipient: Recipients,
                      actor: User) -> State:
        state = State.NEW
        if actor.role == Role.MANAGER:
            state = State.CONFIRMED
        elif recipient.manager is None:
            state = State.CONFIRMED
        return state

    def update(self,
              fsm: TicketLifecycle,
              actor:User,
              cmd: CmdChangeState)-> tuple[TicketView, Recipients]:
        tickets = self.uow.tickets.get({"ticket_id": cmd.ticket_id})
        if not tickets:
            raise CoreValidationBreak("Ticket not found")
        ticket = tickets[0]
        old_state = ticket.state.name
        rule = self.uow.rule.get_rules({'code': ticket.code})[0]
        cmd_policy_map = {
            State.CANCELLED: 'reject',
            State.CONFIRMED: 'confirm',
            State.IN_PROGRESS: 'assign',
            State.WAITING_EXTERNAL: 'on_waiting',
            State.RESOLVED: 'finish',
            State.CLOSED: 'close'
        }
        action = cmd_policy_map.get(cmd.new_state)
        if not actor:
            raise CoreValidationBreak(f"Unsupported state transition to {cmd.new_state}")
        self.control.can(actor,'lead_ticket',action)
        fsm.check_prohibit_step(first_state=ticket.state,second_state= cmd.new_state)

        ticket.state = cmd.new_state
        ticket.context.comment = cmd.comment
        self.uow.tickets.update()

        self.uow.tickets.insert_history(ticket.id,
                                        datetime.now().strftime(DATE_FORMAT),
                                        actor.id,
                                        'current_state',
                                        old_state,
                                        cmd.new_state)
        recipient =  RecipientResolver.get_update_recipient(action,self.uow,rule,ticket)
        view = TicketView(ticket,rule.name,actor.branch_name)
        return view, recipient


    def get(self, actor:User,
            cmd:QueryGetTicket)-> list[TicketView]:
        self.control.can(actor,'lead_ticket', 'get_ticket')
        cmd = PolicyUser.validate_cmd(cmd,actor)
        tickets = self.uow.tickets.get(cmd.dict())
        return tickets

    def history(self,
                actor:User,
                cmd:QueryGetHistoryTicket):
        self.control.can(actor,'lead_ticket', 'get_history')
        cmd = PolicyUser.validate_cmd(cmd, actor)
        history = self.uow.tickets.get_history(cmd.dict())
        return history



