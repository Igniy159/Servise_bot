from aiogram import BaseMiddleware
from core.exceptions import PermissionDenied
from repository.unit_of_work import main_factory_uow
from service.controllers import AuthController
from api.handlers import FIRST_OWNER

class AuthMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler,
                       event,
                       data):

        tg_user = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        uow = main_factory_uow()
        try:
            user = AuthController(uow_example=uow,
                                  user_name=tg_user.username,
                                  api_user_id=tg_user.id,
                                  first_owner_id=int(FIRST_OWNER)).auth()

        except PermissionDenied:
            if hasattr(event, "answer"):
                await event.answer(
                    f"Вы не зарегистрированы.Обратитесь к администратору.\nВаш id: {tg_user.id}"
                )
            return None
        data['user'] = user
        data['uow'] = uow
        return await handler(event, data)
