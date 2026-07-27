from os import getenv
from aiogram import BaseMiddleware
from aiogram.types import Message

from UX_laier.translate import Formatter
from core.exceptions import PermissionDenied, RepositoryError
from service.controllers import AuthController

class AuthMiddleware(BaseMiddleware):
    def __init__(self, uow_factory, raw_config):
        self.uow_factory = uow_factory
        self.raw_config = raw_config

    async def __call__(self,
                       handler,
                       event,
                       data):
        if isinstance(event, Message) and event.text:
            if event.text.startswith("/start"):
                return await handler(event, data)
        tg_user = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        uow = self.uow_factory()
        try:
            with uow:
                user = AuthController(uow_example=uow,
                                      user_name=tg_user.username,
                                      api_user_id=tg_user.id,
                                      first_owner_id=int(getenv('FIRST_OWNER'))).auth()
                data['user'] = user
                data['uow'] = uow
                data['raw_config'] = self.raw_config
                data['formatter'] = Formatter(self.raw_config)
                result = await handler(event, data)
        except PermissionDenied:
            if hasattr(event, "answer"):
                await event.answer(
                    f"Вы не зарегистрированы.Обратитесь к администратору.\nВаш id: {tg_user.id}"
                )
            else:
                await event.answer("У вас нет прав на эту операцию")
            return None
        except RepositoryError:
            await event.answer("Произошла ошибка.")
            return None
        except Exception:
            raise
        return result
