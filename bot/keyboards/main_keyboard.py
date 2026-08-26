from aiogram.types import  InlineKeyboardButton as InB, InlineKeyboardMarkup
from core.ticket_core import User


def get_owner_menu()-> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InB(text="Филиалы",callback_data='branches')],
                   [InB(text='Сотрудники',callback_data='users')],
                    [InB(text='Заявки', callback_data="tickets")],
                        [InB(text='Дашборд', callback_data='dashboard')]
                  ]
    )
    return keyboard

def get_manager_menu()-> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
                [InB(text='Заявки филиала',callback_data='ticket_for_branch')],
                [InB(text='Мои сотрудники',callback_data='my_users')],
                [InB(text='Создать заявку',callback_data='create_ticket')],
                ]
    )
    return keyboard

def get_specialist_menu()-> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InB(text='Заявки отдела', callback_data='ticket_from_depart')]])
    return keyboard

def get_employee_menu()-> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InB(text='Создать заявку',callback_data='create_ticket')]])
    return keyboard


def get_main_menu(actor: User)-> InlineKeyboardMarkup:
    mapper = {
        "EMPLOYEE": get_employee_menu,
        'MANAGER': get_manager_menu,
        'SPECIALIST': get_specialist_menu,
        'OWNER': get_owner_menu
    }
    return mapper[actor.role.name]()

def button_main_menu()-> list[InB]:
    button = [InB(text='🏠Главное меню',callback_data='main_menu')]
    return button

def get_button_main():
    keyboard= InlineKeyboardMarkup(inline_keyboard=[button_main_menu()])
    return keyboard

def get_button_back()-> list[InB]:
    button = [InB(text='🔙Назад',callback_data='back')]
    return button


def get_open_dash_menu(url)->InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InB(text='📖Открыть дашборд',url=url)]])
    keyboard.inline_keyboard.append(button_main_menu())
    return keyboard
