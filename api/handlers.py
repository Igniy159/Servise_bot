from os import getenv
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import Router, F
from dotenv import load_dotenv

from core.exceptions import PermissionDenied
from repository.unit_of_work import main_factory_uow
from service.controllers import AuthController
from api.keyboards import get_main_menu
from api.midleware import AuthMiddleware


load_dotenv()
FIRST_OWNER = getenv('FIRST_OWNER')
router = Router()
auth_router = Router()
router.message.middleware(AuthMiddleware())

@auth_router.message(Command('start'))
async def auth(message:Message):
    uow = main_factory_uow()
    try:
        user = AuthController(uow_example=uow,
                       user_name=message.from_user.username,
                       api_user_id=message.from_user.id,
                       first_owner_id= int(FIRST_OWNER)).auth()
        menu = get_main_menu(user)
        await message.answer("Добро пожаловать в систему",
                              reply_markup=menu)
    except PermissionDenied:
        await message.answer(f"""Вы не зарегистрированы в системе. Обратитесь к администратору.
                             Ваш id: {message.from_user.id}""")

@router.message(F.text.title() == 'Филиалы')
async def branches(message: Message):
    pass
