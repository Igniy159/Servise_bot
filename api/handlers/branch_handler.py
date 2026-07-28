"""
Telegram handlers for branch management.

This module contains handlers responsible for branch-related user flows:
- displaying branch management menu;
- retrieving branch list;
- creating new branches;
- renaming existing branches;
- deleting branches.

Handlers in this module do not contain business logic.
They handle Telegram events, collect user input through FSM,
create application commands and delegate operations to BranchService.

FSM states:
    BranchState.waiting_for_branch_name:
        Waiting for a new branch name during branch creation.

    BranchState.waiting_for_new_branch_name:
        Waiting for a new branch name during branch rename flow.

Callback data format:
    rename:<branch_id>
    delete:<branch_id>

Dependencies are injected through aiogram middleware:
    user:
        Authenticated application user.

    uow:
        Unit of Work instance for repository access.

    raw_config:
        Application configuration containing roles and permissions.
"""
from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from api.command import QueryReceiveBranch, CmdCreateBranch, CmdRenameBranch, CmdDeleteBranch
from api.keyboards.branch_keyboard import get_branch_menu,get_branch_keyboard
from core.ticket_core import User, Branch
from repository.unit_of_work import UoW
from service.branch_service import BranchService


branch_router = Router()

@branch_router.message(F.text.title() == 'Филиалы')
async def branches_menu(message: Message):
    menu = get_branch_menu()
    await message.answer(text='Панель управления филиалами',reply_markup=menu)

@branch_router.callback_query(F.data == 'get_branches')
async def show_branches(callback: CallbackQuery,
                       user: User,
                       uow: UoW,
                       raw_config:dict):
    command = QueryReceiveBranch()
    await callback.answer()
    branches = BranchService(uow, user, raw_config['roles']).receive(command)
    if branches:
        msg = "\n".join([str(branch) for branch in branches])
        await callback.message.answer(msg)
    else:
        await callback.message.answer('Филиалы не найдены. Создайте новый филиал')

def get_branches(user: User,
                       uow: UoW,
                       raw_config:dict)-> list[Branch]:
    command = QueryReceiveBranch()
    branches = BranchService(uow, user, raw_config['roles']).receive(command)
    return branches


class BranchState(StatesGroup):
    """
    FSM states used during branch management workflows.

    States store temporary user interaction context between
    different Telegram events.

    Attributes:
        waiting_for_branch_name:
            User entered branch creation flow and must provide a name.

        waiting_for_new_branch_name:
            User selected existing branch and must provide a new name.
    """
    waiting_for_branch_name = State()
    waiting_for_new_branch_name = State()

@branch_router.callback_query(F.data == 'create_branch')
async def create_branch_start(callback: CallbackQuery,
                          state: FSMContext):
    await callback.message.answer('Введите название нового филиала:')
    await state.set_state(BranchState.waiting_for_branch_name)

@branch_router.message(BranchState.waiting_for_branch_name)
async def create_branch_finish(message: Message,
                               user: User,
                                uow: UoW,
                                raw_config: dict,
                               state: FSMContext):
    command = CmdCreateBranch(name=message.text)
    branch = BranchService(uow=uow,
                           user=user,
                           accesses=raw_config['roles']).create(command)
    await message.answer(f"{str(branch)} был успешно создан")
    await state.clear()

@branch_router.callback_query(F.data == 'rename_branch')
async def rename_branch_start(callback: CallbackQuery,
                                user: User,
                                uow: UoW,
                                raw_config: dict
                                ):
    branches = get_branches(user, uow, raw_config)
    if not branches:
        await callback.message.answer('Филиалы не найдены. Создайте новый филиал')
    else:
        keyboard = get_branch_keyboard(branches,'rename_branch')
        await callback.message.answer(text="Выберите филиал чтоб его переименовать:",
                                      reply_markup= keyboard )

@branch_router.callback_query(F.data.startswith('rename_branch:'))
async def rename_branch_set_name(callback: CallbackQuery,
                                state: FSMContext
                                 ):
    branch_id = int(callback.data.split(':')[1])
    await callback.answer()
    await callback.message.answer(text="Напишите новое имя для филиала")
    await state.update_data(branch_id= branch_id)
    await state.set_state(BranchState.waiting_for_new_branch_name)

@branch_router.message(BranchState.waiting_for_new_branch_name)
async def rename_branch_finish(message: Message,
                               state: FSMContext,
                               user: User,
                               raw_config:dict,
                               uow: UoW):
    data = await state.get_data()
    command = CmdRenameBranch(branch_id=data['branch_id'],
                              new_name= message.text)
    branch = BranchService(uow, user, raw_config['roles']).rename(command)
    await message.answer(text=f'Филиал {branch.id} был успешно переименован')
    await state.clear()


@branch_router.callback_query(F.data == 'delete_branch')
async def delete_branch_start(callback: CallbackQuery,
                              user: User,
                              uow: UoW,
                              raw_config: dict
                              ):
    branches = get_branches(user, uow, raw_config)
    if not branches:
        await callback.message.answer('Филиалы не найдены. Создайте новый филиал')
    else:
        keyboard = get_branch_keyboard(branches,'delete_branch')
        await callback.message.answer(text="Выберите филиал чтоб его удалить:",
                                      reply_markup= keyboard )


@branch_router.callback_query(F.data.startswith('delete_branch:'))
async def delete_branch_finish(callback: CallbackQuery, user: User,
                               raw_config:dict,
                               uow: UoW):
    branch_id = int(callback.data.split(':')[1])
    command = CmdDeleteBranch(branch_id= branch_id)
    branch = BranchService(uow, user, raw_config['roles']).delete(command)
    await callback.message.answer(f"Филиал {branch.name} был удалён")
