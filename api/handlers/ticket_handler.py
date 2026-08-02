from aiogram import F, Router
from aiogram.types import Message
from api.keyboards.ticket_keyboard import get_departments_menu
from api.midleware import RequestContext

ticket_router = Router()

@ticket_router.message(F.text.lower() == "создать заявку")
async def users_menu(message: Message,
                     ctx: RequestContext):
    depart = ctx.uow.dep_mapper.get_all_depart()
    keyboard = get_departments_menu(ctx.formatter, depart)
    await message.answer(text='Выберите отдел: ', reply_markup=keyboard)
