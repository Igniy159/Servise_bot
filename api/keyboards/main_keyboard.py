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
        keyboard=[[KB(text='Заявки')],
                  [KB(text='Сотрудники')],
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
        keyboard=[[KB(text="Срочные уведомления"), KB(text='ARS служба')],
                  [KB(text='IT отдел'), KB(text='Служба безопасности')],
                   [KB(text='Склад'), KB(text='Инвентарь')],
                   [KB(text='Бухгалтерия'), KB(text='HR отдел')],
                   [KB(text='Сервис менеджер'), KB(text='Маркетинг')]
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
    return mapper[actor.role]()
