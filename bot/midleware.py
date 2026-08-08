from os import getenv
from typing import Optional
from aiogram import BaseMiddleware, Bot
from UX_laier.formatter import Formatter
from core.exceptions import PermissionDenied, RepositoryError
from core.ticket_core import User
from repository.unit_of_work import UowFactory, UoW
from service.controllers import AuthController, ServiceFactory

class RequestContext:
    def __init__(self,
                 uow: UoW,
                 actor: User,
                 raw_config: dict,
                 services: ServiceFactory,
                 bot: Optional[Bot] = None):
        self.service_branch = services.branch_service
        self.service_user = services.user_service
        self.service_ticket = services.ticket_service
        self.service_alert = services.alert_service
        self.uow = uow
        self.actor = actor
        self.raw_config = raw_config
        self.formatter = Formatter(self.raw_config)
        self.bot = bot


class AuthMiddleware(BaseMiddleware):
    def __init__(self,
                 uow_factory: UowFactory,
                 raw_config:dict,
                 fake_user_id: Optional[int]=None):
        self.uow_factory = uow_factory
        self.raw_config = raw_config
        self.fake_user_id = fake_user_id

    async def __call__(self,
                       handler,
                       event,
                       data):
        tg_user = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)
        uow = self.uow_factory()
        try:
            with uow:
                service_factory = ServiceFactory(self.raw_config,uow)
                user = AuthController(
                                      user_name=tg_user.username,
                                      api_user_id=self.fake_user_id or tg_user.id,
                                      first_owner_id=int(getenv('FIRST_OWNER')),
                                    uow=uow,
                    user_service= service_factory.user_service).auth()
                data['ctx'] = RequestContext(uow,
                                             user,
                                             self.raw_config,
                                             service_factory,
                                             data.get(''))
                result = await handler(event, data)
                uow.con.commit()
        except PermissionDenied:
            if hasattr(event, "answer"):
                await event.answer(
                    f"Вы не зарегистрированы.Обратитесь к администратору.\nВаш id: {tg_user.id}"
                )
            else:
                await event.answer("У вас нет прав на эту операцию")
        except RepositoryError:
            await event.answer("Произошла ошибка.")
            return None
        except Exception:
            raise
        return result
