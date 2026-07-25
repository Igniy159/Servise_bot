from os import getenv
from aiogram import Router
from dotenv import load_dotenv
from api.handlers.branch_handler import branch_router
from api.handlers.user_handler import user_router
from api.handlers.ticket_handler import ticket_router
from api.keyboards.main_keyboard import get_main_menu
from core.exceptions import PermissionDenied
from repository.unit_of_work import main_factory_uow
from service.controllers import AuthController
from aiogram.filters import Command
from aiogram.types import Message

auth_router = Router()
main_routers = (branch_router, user_router, ticket_router, auth_router)


@auth_router.message(Command('start'))
async def auth(message:Message):
    uow = main_factory_uow()
    load_dotenv()
    try:
        user = AuthController(uow_example=uow,
                       user_name=message.from_user.username,
                       api_user_id=message.from_user.id,
                       first_owner_id= int(getenv('FIRST_OWNER'))).auth()
        menu = get_main_menu(user)
        await message.answer(f"Добро пожаловать в систему {user.name}. Ваша роль {user.role}",
                              reply_markup=menu)
    except PermissionDenied:
        await message.answer(f"""Вы не зарегистрированы в системе. Обратитесь к администратору.
                             Ваш id: {message.from_user.id}""")

