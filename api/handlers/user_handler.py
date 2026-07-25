from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from UX_laier.translate import user_formatter, Formatter
from api.command import QueryReceiveUser, CmdCreateUser
from api.keyboards.user_keyboard import get_user_menu
from core.ticket_core import User
from repository.unit_of_work import UoW
from service.user_service import UserService


user_router = Router()

@user_router.message(F.text.lower() == "сотрудники")
async def users_menu(message: Message):
    menu = get_user_menu()
    await message.answer(text='Панель управления сотрудниками', reply_markup=menu)

@user_router.callback_query(F.data == 'get_all_users')
async def get_users(callback: CallbackQuery,
                    user: User,
                    uow: UoW,
                    raw_config: dict):
    command = QueryReceiveUser(user_activity=1)
    service = UserService(raw_config,uow)
    users = service.get(actor=user, cmd=command)
    frm = Formatter(raw_config)
    text = "\n".join(frm.user_formatter(u) for u in users)
    await callback.message.answer(text)



