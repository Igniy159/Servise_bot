
from fastapi import APIRouter
from api.dependencies import get_ctx

from core.schemas import (QueryGetTicket,
                          CmdChangeState,
                          CmdChangeUser,
                          QueryReceiveUser,
                          QueryReceiveBranch,
                        QueryGetHistoryTicket,
                          QueryGetAlerts)
from fastapi import Depends,  status
from core.ticket_core import TicketLifecycle
from bot.midleware import RequestContext

private_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(get_ctx)])


@private_router.get('/branches')
def get_branches(query: QueryReceiveBranch = Depends(),
                 ctx: RequestContext = Depends(get_ctx)):
    return ctx.service_branch.receive(ctx.actor, query)

@private_router.get('/users')
def get_users(query: QueryReceiveUser = Depends(),
              ctx: RequestContext = Depends(get_ctx)):
    return ctx.service_user.get(ctx.actor,query)

@private_router.get('/tickets')
def get_tickets(query: QueryGetTicket = Depends(),
                ctx: RequestContext = Depends(get_ctx)):
    return ctx.service_ticket.get(ctx.actor,query)

@private_router.get('/departments')
def get_department(ctx: RequestContext = Depends(get_ctx)):
    return ctx.uow.dep_mapper.get_all_depart()

@private_router.get('/tickets/{ticket_id}/history')
def get_ticket_history(query = QueryGetHistoryTicket,
                       ctx: RequestContext = Depends(get_ctx)):
    return ctx.service_ticket.history(ctx.actor, query)

@private_router.get('/alerts')
def get_alerts(query = QueryGetAlerts,
               ctx: RequestContext =Depends(get_ctx)):
    return ctx.service_alert.get(query,ctx.actor)


@private_router.post('/tickets/change-state', status_code=status.HTTP_200_OK)
def change_ticket_state(cmd: CmdChangeState,
                        ctx: RequestContext = Depends(get_ctx)):
    fsm = TicketLifecycle(ctx.raw_config)
    return ctx.service_ticket.update(fsm,ctx.actor,cmd)


@private_router.post('/users/change', status_code=status.HTTP_200_OK)
def change_user_attributes(cmd: CmdChangeUser,
                           ctx: RequestContext = Depends(get_ctx)):
    return ctx.service_user.change(ctx.actor,cmd)
