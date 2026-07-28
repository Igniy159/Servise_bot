from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as InB
from core.ticket_core import Department, User
from core.enums import Role
from UX_laier.translate import Formatter


def get_user_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text='Все сотрудники',callback_data='get_all_users')],
            [InB(text='Добавить сотрудника',callback_data='create_user')],
            [InB(text='Пользователи филиалов',callback_data='branch_users')],
            [InB(text='Специалисты служб', callback_data='depart_users')]
        ]
    )
    return keyboard

def get_department_keyboard(formater: Formatter,
                            departments: list[Department],
                            action:str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text=formater.translate(depart.name), callback_data=f'{action}:{depart.id}')]
             for depart in departments
        ]
    )
    return keyboard
def get_user_keyboard(users: list[User], formatter):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text=f" 👤{user.name} | {formatter.translate(user.role.name)}",
                 callback_data=f'user_id:{user.id}')]
            for user in users
        ]
    )
    return keyboard

def get_roles_keyboard(formater: Formatter,
                       action:str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text=formater.translate(role.value), callback_data=f'{action}:{role.value}')]
             for role in Role
        ]
    )
    return keyboard

def get_actions_from_user():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text='Переименовать сотрудника',callback_data='user_action:rename')],
            [InB(text='Изменить сотрудника',callback_data='user_action:change')],
            [InB(text='Удалить сотрудника',callback_data='user_action:delete')]
        ]
    )
    return keyboard
