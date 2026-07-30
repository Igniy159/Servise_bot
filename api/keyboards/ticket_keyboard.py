from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as InB
from UX_laier.translate import Formatter
from core.ticket_core import Department


def get_employee_create_ticket(formatter: Formatter,
                             departments: list[Department]):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
        [InB(text=formatter.translate(depart.name),callback_data=f'{depart.name}:{depart.id}')]
        for depart in departments
]
)
    return keyboard
