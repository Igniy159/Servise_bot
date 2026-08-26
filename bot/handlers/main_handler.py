import datetime
import os
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from jose import jwt
from bot.handlers.branch_handler import branch_router
from bot.handlers.user_handler import user_router
from bot.handlers.ticket_handler import ticket_router
from bot.keyboards.main_keyboard import get_main_menu, get_open_dash_menu
from bot.midleware import RequestContext
from core.exceptions import PermissionDenied
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

auth_router = Router()
main_routers = (branch_router, user_router, ticket_router, auth_router)


@auth_router.message(Command('start'))
async def auth(message:Message,
            ctx: RequestContext):
    try:
        menu = get_main_menu(ctx.actor)
        await message.answer(
            text=f'Добро пожаловать в систему, {ctx.actor.name}!', reply_markup=ReplyKeyboardRemove())
        await message.answer(
            text=f"""Ваша роль: {ctx.formatter.translate(ctx.actor.role.name)}""",
                              reply_markup=menu)
    except PermissionDenied:
        await message.answer(f"""Вы не зарегистрированы в системе. Обратитесь к администратору.
                             Ваш id: {message.from_user.id}""")

@auth_router.callback_query(F.data == 'main_menu')
async def main_menu(callback: CallbackQuery,
                    ctx: RequestContext,
                    state: FSMContext):
    menu = get_main_menu(ctx.actor)
    await state.clear()
    await callback.message.edit_text('🏠 Главное меню: ', reply_markup=menu)

@auth_router.callback_query(F.data =="dashboard")
async def dashboard(callback: CallbackQuery,
                    ctx: RequestContext):
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ALGORITHM = "HS256"
    DASHBOARD_PUBLIC_URL = os.getenv('DASHBOARD_PUBLIC_URL')
    expiration_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=60)
    payload = {
    'sub': ctx.actor.api_id,
    'exp': expiration_time}
    token = jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
    url = f'{DASHBOARD_PUBLIC_URL}?token={token}'
    menu = get_open_dash_menu(url)
    await callback.message.edit_text(text="Перейдите по ссылке для просмотра", reply_markup=menu)
    await callback.answer()
