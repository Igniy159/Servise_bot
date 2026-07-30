from aiogram.types import ReplyKeyboardMarkup, KeyboardButton as KB
from core.ticket_core import User


def get_owner_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KB(text="Филиалы")],
                   [KB(text='Сотрудники')],
                    [KB(text='Заявки')]
                  ],
        resize_keyboard=True)
    return keyboard

def get_manager_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
                [KB(text='Заявки')],
                [KB(text='Мои сотрудники')],
                ],
        resize_keyboard=True)
    return keyboard

def get_specialist_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KB(text='Активные заявки')]
                  ],
        resize_keyboard=True)
    return keyboard

def get_employee_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
                [KB(text="Критическое событие 🚨")],
                [KB(text='Создать заявку')]
                ],
        resize_keyboard=True)
    return keyboard


def get_main_menu(actor: User)-> ReplyKeyboardMarkup:
    mapper = {
        "EMPLOYEE": get_employee_menu,
        'MANAGER': get_manager_menu,
        'SPECIALIST': get_specialist_menu,
        'OWNER': get_owner_menu
    }
    return mapper[actor.role.name]()
