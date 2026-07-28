from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from UX_laier.translate import Formatter
from api.command import QueryReceiveUser, CmdCreateUser, CmdDeleteUser, CmdChangeUser, CmdRenameUser
from api.keyboards.branch_keyboard import get_branch_keyboard
from api.keyboards.user_keyboard import get_user_menu, get_roles_keyboard, get_department_keyboard, get_user_keyboard, \
    get_actions_from_user
from core.enums import Role
from core.ticket_core import User, Branch, Department
from repository.unit_of_work import UoW
from service.user_service import UserService

user_router = Router()
@user_router.message(F.text.lower() == "сотрудники")
async def users_menu(message: Message):
    menu = get_user_menu()
    await message.answer(text='Панель управления сотрудниками', reply_markup=menu)


@user_router.callback_query(F.data == 'get_all_users')
async def get_users(callback: CallbackQuery,
                    user: User,
                    uow: UoW,
                    raw_config: dict):
    await callback.answer()
    command = QueryReceiveUser()
    service = UserService(raw_config, uow)
    users = service.get(actor=user, cmd=command)
    frm = Formatter(raw_config)
    text = "\n".join(frm.user_formatter(u) for u in users)
    await callback.message.edit_text(text)


class UserState(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_role = State()
    waiting_for_depart = State()
    waiting_for_branch = State()
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
                           formatter: Formatter):
    await state.update_data(user_name=message.text)
    await state.set_state(UserState.waiting_for_role)
    keyboard = get_roles_keyboard(formatter, 'create_user')
    await message.answer(text="Выберите роль сотрудника: ", reply_markup=keyboard)


@user_router.callback_query(UserState.waiting_for_role)
async def processing_user_role(callback: CallbackQuery,
                                state: FSMContext,
                                formatter: Formatter,
                                uow: UoW):
    await callback.answer()
    role = Role(callback.data.split(':')[1])
    await state.update_data(user_role=role)
    if role == Role.OWNER:
        await state.set_state(UserState.waiting_finish)
    elif role == Role.SPECIALIST:
        await state.set_state(UserState.waiting_for_depart)
        depart = [Department(d) for d in uow.dep_mapper.get_all_depart()]
        keyboard = get_department_keyboard(formatter, depart, 'create_user')
        await callback.message.answer(text="Выберите отдел: ", reply_markup=keyboard)
    else:
        await state.set_state(UserState.waiting_for_branch)
        branches = [Branch(b) for b in uow.branches.get()]
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
                             uow: UoW,
                             raw_config: dict,
                             user: User,
                             formatter: Formatter):
    await callback.answer()
    data = await state.get_data()
    service = UserService(raw_config, uow)
    if data['mode'] == 'create':
        command = CmdCreateUser(
            user_name=data['user_name'],
            role=data['user_role'],
            api_user_id=data['user_id'],
            depart_id=data.get('user_depart'),
            branch_id=data.get('user_branch')
        )
        with uow:
            user = service.create(user, command)
        await callback.message.answer(
            f'Пользователь: {formatter.user_formatter(user)} был добавлен')
        await state.clear()
    else:

        command = CmdChangeUser(
            user_id=data['user_id'],
            role=data['user_role'],
            user_depart_id=data.get('user_depart'),
            user_branch_id=data.get('user_branch'))
        print('Я команда', command)
        with uow:
            user = service.change(actor=user, cmd=command)
        await callback.message.answer(f'Пользователь: {formatter.user_formatter(user)} был изменен')
        await state.clear()

@user_router.callback_query(F.data == 'branch_users')
async def get_branch_users(callback: CallbackQuery,
                           uow: UoW):
    await callback.answer()
    with uow:
        branches = [Branch(b) for b in uow.branches.get()]
    keyboard = get_branch_keyboard(branches, 'branch_users')
    await callback.message.answer(text='Выберите филиал:', reply_markup=keyboard)


@user_router.callback_query(F.data == 'depart_users')
async def get_depart_users(callback: CallbackQuery,
                           uow: UoW,
                           formatter: Formatter):
    await callback.answer()
    with uow:
        depart = [Department(d) for d in uow.dep_mapper.get_all_depart()]
    keyboard = get_department_keyboard(formatter, depart, 'depart_users')
    await callback.message.answer(text='Выберите отдел:', reply_markup=keyboard)


@user_router.callback_query( F.data.startswith('branch_users') |
    F.data.startswith('depart_user'))
async def get_users_menu(callback: CallbackQuery,
                         user: User,
                         uow: UoW,
                         raw_config:dict,
                         formatter: Formatter,
                         state: FSMContext):
    await callback.answer()
    data_type, obj_id = callback.data.split(':')
    obj_id = int(obj_id)
    service = UserService(raw_config,uow)
    await state.update_data(source_type=data_type,source_id=obj_id)
    if data_type == 'branch_users':
        command = QueryReceiveUser(user_branch_id=obj_id)
    else:
        command = QueryReceiveUser(user_depart_id=obj_id)
    users = service.get(user,command)
    if not users:
        await callback.message.answer("Пользователей нет ")
    else:
        keyboard = get_user_keyboard(users, formatter)
        await callback.message.answer(
            text="Сотрудники: ",
            reply_markup=keyboard)

@user_router.callback_query(F.data.startswith('user_id'))
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
                               raw_config:dict,
                               user: User,
                                formatter: Formatter,
                               uow: UoW):
    await callback.answer()
    action = callback.data.split(':')[1]
    if action == 'rename':
        await state.set_state(UserState.rename_user)
        await callback.message.answer('Введите новое имя для сотрудника: ')
    elif action == 'delete':
        data = await state.get_data()
        service = UserService(raw_config, uow)
        command = CmdDeleteUser(user_id=data['user_id'])
        with uow:
            user = service.delete(actor=user, cmd=command)
        await callback.message.answer(f'Пользователь: {formatter.user_formatter(user)} был удалён')
        await state.clear()
    elif action == 'change':
        await state.set_state(UserState.waiting_for_role)
        await state.update_data(mode='change')
        keyboard = get_roles_keyboard(formatter, 'change_user')
        await callback.message.answer('Выберите новую роль для сотрудника: ', reply_markup=keyboard)


@user_router.message(UserState.rename_user)
async def rename_user(message: Message,
                      state: FSMContext,
                      uow: UoW,
                      raw_config: dict,
                      user: User,
                      formatter: Formatter
                      ):
    service = UserService(raw_config, uow)
    data = await state.get_data()
    new_name = message.text
    command = CmdRenameUser(user_id=data['user_id'],
                            user_name=new_name)
    with uow:
        user = service.rename(actor=user, cmd=command)
    await message.answer(f'Пользователь: {formatter.user_formatter(user)} был изменён')
    await state.clear()
