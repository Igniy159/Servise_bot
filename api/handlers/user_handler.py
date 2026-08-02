from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from api.command import (QueryReceiveUser,
                         CmdCreateUser,
                         CmdDeleteUser,
                         CmdChangeUser,
                         CmdRenameUser)
from api.handlers.branch_handler import get_branches
from api.keyboards.branch_keyboard import get_branch_keyboard
from api.keyboards.user_keyboard import (get_user_for_owner_menu,
                                         get_roles_keyboard,
                                         get_department_keyboard,
                                         get_user_keyboard,
                                         get_actions_from_user, get_user_for_manager_menu)
from api.midleware import RequestContext
from core.enums import Role

user_router = Router()
@user_router.message(F.text.lower() == "сотрудники")
async def users_menu(message: Message):
    menu = get_user_for_owner_menu()
    await message.answer(text='Панель управления сотрудниками', reply_markup=menu)


def get_department(ctx:RequestContext):
    return ctx.uow.dep_mapper.get_all_depart()

@user_router.callback_query(F.data == 'get_all_users')
async def get_all_users(callback: CallbackQuery,
                    ctx: RequestContext):
    await callback.answer()
    cmd = QueryReceiveUser()
    users = ctx.service_user.get(ctx.actor,cmd)
    text = "\n".join(ctx.formatter.user_formatter(u) for u in users)
    await callback.message.edit_text(text)

class UserState(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_role = State()
    waiting_for_depart = State()
    waiting_for_branch = State()
    user_operations = State()
    waiting_finish = State()
    rename_user = State()

@user_router.callback_query(F.data == 'create_user')
async def start_create_user(callback: CallbackQuery,
                            state: FSMContext):
    await state.set_state(UserState.waiting_for_id)
    await state.update_data(mode='create')
    await callback.answer()
    await callback.message.answer('Введите TG id сотрудника:')


@user_router.message(UserState.waiting_for_id)
async def processing_user_id(message: Message,
                        state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID должен быть числом")
        return
    await state.update_data(user_id=message.text)
    await state.set_state(UserState.waiting_for_name)
    await message.answer(text="Введите имя сотрудника: ")


@user_router.message(UserState.waiting_for_name)
async def processing_user_name(message: Message,
                           state: FSMContext,
                           ctx: RequestContext):
    await state.update_data(user_name=message.text)
    await state.set_state(UserState.waiting_for_role)
    keyboard = get_roles_keyboard(ctx.formatter, 'create_user')
    await message.answer(text="Выберите роль сотрудника: ", reply_markup=keyboard)


@user_router.callback_query(UserState.waiting_for_role)
async def processing_user_role(callback: CallbackQuery,
                                state: FSMContext,
                                ctx: RequestContext):
    await callback.answer()
    role = Role(callback.data.split(':')[1])
    await state.update_data(user_role=role)
    if role == Role.OWNER:
        await state.set_state(UserState.waiting_finish)
    elif role == Role.SPECIALIST:
        await state.set_state(UserState.waiting_for_depart)
        depart = get_department(ctx)
        keyboard = get_department_keyboard(ctx.formatter, depart, 'create_user')
        await callback.message.answer(text="Выберите отдел: ", reply_markup=keyboard)
    else:
        await state.set_state(UserState.waiting_for_branch)
        branches = get_branches(ctx)
        keyboard = get_branch_keyboard(branches, 'create_user')
        await callback.message.answer(text="Выберите филиал: ", reply_markup=keyboard)


@user_router.callback_query(UserState.waiting_for_depart)
async def processing_depart_user(callback: CallbackQuery,
                             state: FSMContext):
    await callback.answer()
    depart_id = callback.data.split(':')[1]
    await state.update_data(user_depart=depart_id)
    await state.set_state(UserState.waiting_finish)


@user_router.callback_query(UserState.waiting_for_branch)
async def processing_branch_user(callback: CallbackQuery,
                             state: FSMContext):
    await callback.answer()
    branch_id = callback.data.split(':')[1]
    await state.update_data(user_branch=branch_id)
    await state.set_state(UserState.waiting_finish)


@user_router.callback_query(UserState.waiting_finish)
async def finish_user(callback: CallbackQuery,
                             state: FSMContext,
                             ctx: RequestContext):
    await callback.answer()
    data = await state.get_data()
    if data['mode'] == 'create':
        command = CmdCreateUser(
            user_name=data['user_name'],
            role=data['user_role'],
            api_user_id=data['user_id'],
            depart_id=data.get('user_depart'),
            branch_id=data.get('user_branch')
        )
        user = ctx.service_user.create(ctx.actor,command)
        await callback.message.answer(
            f'Пользователь: {ctx.formatter.user_formatter(user)} был добавлен')
        await state.clear()
    else:
        command = CmdChangeUser(
            user_id=data['user_id'],
            role=data['user_role'],
            depart_id=data.get('user_depart'),
            branch_id=data.get('user_branch'))
        user = ctx.service_user.change(actor=ctx.actor, cmd=command)
        await callback.message.answer(
            f'Пользователь: {ctx.formatter.user_formatter(user)} был изменен')
        await state.clear()

@user_router.callback_query(F.data == 'branch_users')
async def get_branch_users(callback: CallbackQuery,
                           ctx: RequestContext):
    await callback.answer()
    branches = get_branches(ctx)
    keyboard = get_branch_keyboard(branches, 'branch_users')
    await callback.message.answer(text='Выберите филиал:', reply_markup=keyboard)

@user_router.callback_query(F.data == 'depart_users')
async def get_depart_users(callback: CallbackQuery,
             ctx: RequestContext):
    await callback.answer()
    depart = get_department(ctx)
    keyboard = get_department_keyboard(ctx.formatter, depart, 'depart_users')
    await callback.message.answer(text='Выберите отдел:', reply_markup=keyboard)


@user_router.callback_query( F.data.startswith('branch_users') |
    F.data.startswith('depart_user'))
async def get_users_menu(callback: CallbackQuery,
                        ctx: RequestContext,
                         state: FSMContext):
    await callback.answer()
    data_type, obj_id = callback.data.split(':')
    obj_id = int(obj_id)
    await state.update_data(source_type=data_type,source_id=obj_id)
    await state.set_state(UserState.user_operations)
    if data_type == 'branch_users':
        command = QueryReceiveUser(branch_id=obj_id)
    else:
        command = QueryReceiveUser(depart_id=obj_id)
    users = ctx.service_user.get(ctx.actor,command)
    if not users:
        await callback.message.answer("Пользователей нет ")
    else:
        keyboard = get_user_keyboard(users, ctx.formatter)
        await callback.message.answer(
            text="Сотрудники: ",
            reply_markup=keyboard)

@user_router.callback_query(UserState.user_operations)
async def get_user_operations(callback: CallbackQuery,
                              state: FSMContext):
    await callback.answer()
    obj_id = callback.data.split(':')[1]
    keyboard = get_actions_from_user()
    await state.update_data(user_id=obj_id)
    await callback.message.answer(text='Выберите действие над сотрудником:',
                                  reply_markup=keyboard)


@user_router.callback_query(F.data.startswith('user_action'))
async def operations_from_user(callback:CallbackQuery,
                               state: FSMContext,
                               ctx: RequestContext):
    await callback.answer()
    action = callback.data.split(':')[1]
    if action == 'rename':
        await state.set_state(UserState.rename_user)
        await callback.message.answer('Введите новое имя для сотрудника: ')
    elif action == 'delete':
        data = await state.get_data()
        command = CmdDeleteUser(user_id=data['user_id'])
        user = ctx.service_user.delete(actor=ctx.actor, cmd=command)
        await callback.message.answer(
            f'Пользователь: {ctx.formatter.user_formatter(user)} был удалён')
        await state.clear()
    elif action == 'change':
        await state.set_state(UserState.waiting_for_role)
        await state.update_data(mode='change')
        keyboard = get_roles_keyboard(ctx.formatter, 'change_user')
        await callback.message.answer('Выберите новую роль для сотрудника: ', reply_markup=keyboard)


@user_router.message(UserState.rename_user)
async def rename_user(message: Message,
                      state: FSMContext,
                    ctx: RequestContext):
    data = await state.get_data()
    new_name = message.text
    command = CmdRenameUser(user_id=data['user_id'],
                            user_name=new_name)
    user = ctx.service_user.rename(actor=ctx.actor, cmd=command)
    await message.answer(
        f'Пользователь: {ctx.formatter.user_formatter(user)} был изменён')
    await state.clear()

class UserManagerState(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_new_name = State()
    waiting_rename = State()
    waiting_delete = State()

@user_router.message(F.text.lower() == 'мои сотрудники')
async def manager_menu(message: Message):
    keyboard = get_user_for_manager_menu()
    await message.answer(text='Панель управления пользователями: ',
                                  reply_markup=keyboard)

@user_router.callback_query(F.data == 'get_my_users')
async def get_manager_users(callback: CallbackQuery,
                            ctx: RequestContext):
    await callback.answer()
    cmd = QueryReceiveUser(branch_id=ctx.actor.branch_id,
                           role_id=ctx.uow.role_mapper.get_roles_id(Role.EMPLOYEE.name))
    users = ctx.service_user.get(ctx.actor,cmd)
    text = "\n".join(ctx.formatter.user_formatter(u) for u in users)
    await callback.message.answer(text=text)

@user_router.callback_query(F.data == 'create_my_user')
async def create_my_user_start(callback: CallbackQuery,
                               state: FSMContext):
    await state.set_state(UserManagerState.waiting_for_id)
    await callback.answer()
    await callback.message.answer('Введите TG ID сотрудника: ')

@user_router.message(UserManagerState.waiting_for_id)
async def processing_my_user_id(message: Message,
                               state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID должен быть числом")
        return
    await state.update_data(user_id=message.text)
    await state.set_state(UserManagerState.waiting_for_name)
    await message.answer(text="Введите имя сотрудника: ")

@user_router.message(UserManagerState.waiting_for_name)
async def create_my_user_finish(message: Message,
                                ctx: RequestContext,
                                state: FSMContext):
    data = await state.get_data()
    user_id = data.get('user_id')
    user_name = message.text
    command = CmdCreateUser(user_name=user_name,
                            api_user_id=user_id,
                            role=Role.EMPLOYEE,
                            branch_id=ctx.actor.branch_id)
    user = ctx.service_user.create(ctx.actor, command)
    await message.answer(
        f'Пользователь: {ctx.formatter.user_formatter(user)} был добавлен')
    await state.clear()

@user_router.callback_query(F.data == 'delete_my_user')
async def delete_my_user(callback: CallbackQuery,
                         state: FSMContext,
                         ctx: RequestContext):
    await state.set_state(UserManagerState.waiting_delete)
    await callback.answer()
    command = QueryReceiveUser(branch_id=ctx.actor.branch_id,
                            role_id=ctx.uow.role_mapper.get_roles_id(Role.EMPLOYEE.name))
    users = ctx.service_user.get(ctx.actor, command)
    keyboard = get_user_keyboard(users, ctx.formatter)
    await callback.message.answer('Выберите сотрудника для удаления', reply_markup=keyboard)

@user_router.callback_query(UserManagerState.waiting_delete)
async def delete_my_user_finish(callback: CallbackQuery,
                         state: FSMContext,
                         ctx: RequestContext):
    await callback.answer()
    user_id = int(callback.data.split(':')[1])
    cmd = CmdDeleteUser(user_id=user_id)
    deletable = ctx.service_user.delete(ctx.actor,cmd)
    await callback.message.answer(
        f'Пользователь: {ctx.formatter.user_formatter(deletable)} был удалён')
    await state.clear()

@user_router.callback_query(F.data == 'rename_my_user')
async def rename_my_user(callback: CallbackQuery,
                         state: FSMContext,
                         ctx: RequestContext):
    await state.set_state(UserManagerState.waiting_rename)
    await callback.answer()
    users = ctx.service_user.get(ctx.actor, QueryReceiveUser(
            branch_id=ctx.actor.branch_id,
            role_id=ctx.uow.role_mapper.get_roles_id(Role.EMPLOYEE.name)))
    keyboard = get_user_keyboard(users, ctx.formatter)
    await callback.message.answer(
        'Выберите сотрудника которого хотите переименовать', reply_markup=keyboard)

@user_router.callback_query(UserManagerState.waiting_rename)
async def rename_my_user_(callback: CallbackQuery,
                         state: FSMContext):
    await callback.answer()
    await state.update_data(user_id=int(callback.data.split(':')[1]))
    await state.set_state(UserManagerState.waiting_for_new_name)
    await callback.message.answer('Введите новое имя для сотрудника:')

@user_router.message(UserManagerState.waiting_for_new_name)
async def rename_my_user_finish(message: Message,
                                state:FSMContext,
                                ctx: RequestContext):
    data = await state.get_data()
    cmd = CmdRenameUser(user_name=message.text,
                        user_id=data.get('user_id'))
    user = ctx.service_user.rename(ctx.actor,cmd)
    await message.answer(
        f'Пользователь: {ctx.formatter.user_formatter(user)} был переименован')
    await state.clear()
