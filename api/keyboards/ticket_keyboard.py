from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as InB
from UX_laier.translate import Formatter
from core.ticket_core import Department, RuleAlert


def get_departments_menu(formatter: Formatter,
                    departments: list[Department]):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
        [InB(text=formatter.translate(depart.name),callback_data=f'{depart.name}:{depart.id}')]
        for depart in departments
]
)
    return keyboard

def get_alerts_menu(formatter: Formatter,
                    alerts: list[RuleAlert]):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text= formatter.translate(rule.name_alert),
                 callback_data=f'{rule.name_alert}:{rule.code_alert}')]
        for rule in alerts
            ])
    return keyboard

