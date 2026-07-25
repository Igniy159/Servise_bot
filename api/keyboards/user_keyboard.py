from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as InB


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

# def get_user_keyboard(branches: list, action: str):
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard= [
#             [InB(text=f'{branch.name}',callback_data=f'{action}_branch:{branch.id}')]
#             for branch in branches
#         ]
#     )
#     return keyboard