from aiogram import Router, F
from aiogram.fsm.context import FSMContext

from bot.handlers.branch_handler import branch_router
from bot.handlers.user_handler import user_router
from bot.handlers.ticket_handler import ticket_router
from bot.keyboards.main_keyboard import get_main_menu
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
