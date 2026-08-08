import datetime
from fastapi import FastAPI, APIRouter
from core.schemas import (QueryGetTicket,
                          CmdChangeState,
                          CmdChangeUser,
                          QueryReceiveUser,
                          QueryReceiveBranch,
                        QueryGetHistoryTicket,
                          QueryGetAlerts)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from jose import jwt, JWTError
from core.enums import Role
from core.loader import load_config
from core.ticket_core import TicketLifecycle
from repository.unit_of_work import UowFactory
from repository.create_migrations import  DB_PATH
from service.controllers import ServiceFactory, AuthController
from bot.midleware import RequestContext
from core.exceptions  import PermissionDenied, RepositoryError
from fastapi import Request

app = FastAPI()
main_factory_uow = UowFactory(DB_PATH)
raw_config = load_config()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth", auto_error=False)

@app.middleware("http")
async def uow_middleware(request: Request, call_next):
    uow = main_factory_uow()
    request.state.uow = uow
    try:
        async with uow:
            response = await call_next(request)
            await uow.commit()
            return response
    except Exception:
        await uow.rollback()
        raise

async def get_ctx(request: Request,
                  token: str = Depends(oauth2_scheme))-> RequestContext:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен авторизации отсутствует")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        api_user_id: int = int(payload.get("sub"))

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или просроченный токен")
    try:
        uow = request.state.uow
        actors = uow.users.get({'api_user_id': api_user_id})
        if not actors:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не обнаружен")
        else:
            actor = actors[0]

        if actor.role != Role.OWNER:
            raise PermissionDenied
        service_factory = ServiceFactory(raw_config, uow)
        ctx = RequestContext(
        uow=uow,
        actor=actor,
        raw_config=raw_config,
        services=service_factory,
        bot=None)
        return ctx
    except PermissionDenied:
        raise HTTPException(status_code=403, detail="У вас нет прав на эту операцию")
    except RepositoryError:
        raise HTTPException(status_code=500, detail="Ошибка базы данных (RepositoryError)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

public_router = APIRouter(prefix="/api/v1")
private_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(get_ctx)]
)

@public_router.post('/auth',status_code=status.HTTP_200_OK)
def auth(tg_data: dict,
         request: Request):
    api_user_id = tg_data.get('user_id')
    if not api_user_id:
        raise HTTPException(status_code=400,detail='Нет id у пользователя')
    user_name = tg_data.get('username')
    uow = request.state.uow
    service_factory = ServiceFactory(raw_config, uow)
    first_owner_id = int(os.getenv('FIRST_OWNER', 0))
    user = AuthController(
        user_name=user_name,
        api_user_id=api_user_id,
        first_owner_id=first_owner_id,
        uow=uow,
        user_service=service_factory.user_service).auth()
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=60)
    payload = {
    'sub': str(api_user_id),
    'username': user.name,
    'exp': expiration_time
    }
    token = jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer"
    }


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
