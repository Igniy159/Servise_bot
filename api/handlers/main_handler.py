from aiogram import Router

from api.handlers.branch_handler import branch_router
from api.handlers.user_handler import user_router
from api.handlers.ticket_handler import ticket_router
from api.keyboards.main_keyboard import get_main_menu
from api.midleware import RequestContext
from core.exceptions import PermissionDenied
from aiogram.filters import Command
from aiogram.types import Message

auth_router = Router()
main_routers = (branch_router, user_router, ticket_router, auth_router)


@auth_router.message(Command('start'))
async def auth(message:Message,
            ctx: RequestContext):
    try:
        menu = get_main_menu(ctx.actor)
        await message.answer(f"""Добро пожаловать в систему {ctx.actor.name}.
        Ваша роль {ctx.formatter.translate(ctx.actor.role.name)}""",
                              reply_markup=menu)
    except PermissionDenied:
        await message.answer(f"""Вы не зарегистрированы в системе. Обратитесь к администратору.
                             Ваш id: {message.from_user.id}""")
