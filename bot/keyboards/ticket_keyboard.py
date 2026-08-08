from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as InB
from UX_laier.formatter import Formatter
from bot.keyboards.main_keyboard import button_main_menu
from core.ticket_core import Department, Rule
from core.enums import TypeTicket, State


def get_departments_menu(formatter: Formatter,
                    departments: list[Department]):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
        [InB(text=formatter.translate(depart.name),callback_data=f'{depart.name}:{depart.id}')]
        for depart in departments]
)
    keyboard.inline_keyboard.append(button_main_menu())
    return keyboard


def get_rule_menu(formatter: Formatter,
                    rules: list[Rule]):
    set_class_rule = {r.class_rule.name for r in rules}
    if len(set_class_rule) > 1:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InB(text=formatter.translate(rule),
                     callback_data=f'class_rules:{rule}')]
                for rule in set_class_rule])
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InB(text= formatter.translate(rule.name),
                     callback_data=f'rules:{rule.code}')]
            for rule in rules])
    keyboard.inline_keyboard.append(button_main_menu())
    return keyboard

def get_type_object(formatter: Formatter):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text= formatter.translate(TypeTicket.FULL_FAILURE.name),
                 callback_data=f'{TypeTicket.FULL_FAILURE.name}')],
            [InB(text=formatter.translate(TypeTicket.PARTIAL_PROBLEM.name),
                 callback_data=f'{TypeTicket.PARTIAL_PROBLEM.name}')],
            [InB(text=formatter.translate(TypeTicket.MINOR_ISSUE.name),
                 callback_data=f'{TypeTicket.MINOR_ISSUE.name}')]
            ])
    keyboard.inline_keyboard.append(button_main_menu())
    return keyboard

def get_type_request(formatter: Formatter):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text=formatter.translate(TypeTicket.INCIDENT.name),
                 callback_data=f'{TypeTicket.INCIDENT.name}')],
            [InB(text= formatter.translate(TypeTicket.REQUEST.name),
                 callback_data=f'{TypeTicket.REQUEST.name}')]
            ])
    keyboard.inline_keyboard.append(button_main_menu())
    return keyboard

def get_manager_ticket_for_branch():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text="🆕 Новые заявки",
                 callback_data=f'my_ticket:{State.NEW.name}')],
            [InB(text= '👀 В работе',
                callback_data=f'my_ticket:{State.IN_PROGRESS.name}')],
            [InB(text='✅ Ожидают закрытия',
                 callback_data=f'my_ticket:{State.RESOLVED.name}')]
    ]
    )
    keyboard.inline_keyboard.append(button_main_menu())
    return keyboard

def get_specialist_from_depart():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text="🆕 Новые заявки",
                 callback_data=f'my_ticket:{State.CONFIRMED.name}')],
            [InB(text= '⚒️ В работе',
                callback_data=f'my_ticket:{State.IN_PROGRESS.name}')],
            [InB(text='⏸️ Приостановленные',
                 callback_data=f'my_ticket:{State.WAITING_EXTERNAL.name}')],
    ]
    )
    keyboard.inline_keyboard.append(button_main_menu())
    return keyboard
