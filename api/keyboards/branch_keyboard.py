from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton as InB


def get_branch_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InB(text='Активные филиалы',callback_data='get_branches')],
            [InB(text='Создать новый филиал',callback_data='create_branch')],
            [InB(text='Переименовать филиал',callback_data='rename_branch')],
            [InB(text='Удалить филиал', callback_data='delete_branch')]
        ]
    )
    return keyboard

def get_branch_keyboard(branches: list, action: str):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard= [
            [InB(text=f'{branch.name}',callback_data=f'{action}_branch:{branch.id}')]
            for branch in branches
        ]
    )
    return keyboard