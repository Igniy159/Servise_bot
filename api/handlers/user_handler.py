from aiogram.types import Message, CallbackQuery
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from UX_laier.translate import  Formatter
from api.command import QueryReceiveUser, CmdCreateUser
from api.keyboards.branch_keyboard import get_branch_keyboard
from api.keyboards.main_keyboard import get_main_menu
from api.keyboards.user_keyboard import get_user_menu, get_roles_keyboard, get_department_keyboard
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
    command = QueryReceiveUser(user_activity=1)
    service = UserService(raw_config,uow)
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

@user_router.callback_query(F.data == 'create_user')
async def create_user_start(callback: CallbackQuery,
                            state: FSMContext):
    await state.set_state(UserState.waiting_for_id)
    await callback.answer()
    await callback.message.answer('Введите TG id сотрудника:')

@user_router.message(UserState.waiting_for_id)
async def create_user_name(message: Message,
                           state: FSMContext):
    await state.update_data(user_id=message.text)
    await state.set_state(UserState.waiting_for_name)
    await message.answer(text="Введите имя сотрудника: ")

@user_router.message(UserState.waiting_for_name)
async def create_user_role(message: Message,
                           state: FSMContext,
                           formatter: Formatter):
    await state.update_data(user_name=message.text)
    await state.set_state(UserState.waiting_for_role)
    keyboard = get_roles_keyboard(formatter, 'create_user')
    await message.answer(text="Выберите роль сотрудника: ", reply_markup=keyboard)

@user_router.callback_query(UserState.waiting_for_role)
async def create_user_workplace(callback: CallbackQuery,
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
        keyboard = get_department_keyboard(formatter,depart,'create_user')
        await callback.message.answer(text="Выберите отдел: ", reply_markup=keyboard)
    else:
        await state.set_state(UserState.waiting_for_branch)
        branches = [Branch(b) for b in uow.branches.get()]
        keyboard = get_branch_keyboard(branches,'create_user')
        await callback.message.answer(text="Выберите филиал: ", reply_markup=keyboard)

@user_router.callback_query(UserState.waiting_for_depart)
async def create_depart_user(callback: CallbackQuery,
                             state: FSMContext):
    await callback.answer()
    depart_id = callback.data.split(':')[1]
    await state.update_data(user_depart=depart_id)
    await state.set_state(UserState.waiting_finish)

@user_router.callback_query(UserState.waiting_for_branch)
async def create_branch_user(callback: CallbackQuery,
                             state: FSMContext):
    await callback.answer()
    branch_id = callback.data.split(':')[1]
    await state.update_data(user_branch=branch_id)
    await state.set_state(UserState.waiting_finish)

@user_router.callback_query(UserState.waiting_finish)
async def create_user_finish(callback:CallbackQuery,
                             state: FSMContext,
                             uow: UoW,
                             raw_config: dict,
                             user: User,
                             formatter: Formatter):
    await callback.answer()
    data = await state.get_data()
    command = CmdCreateUser(
        user_name= data['user_name'],
        role=data['user_role'],
        api_user_id=data['user_id'],
        depart_id=data.get('user_depart'),
        branch_id=data.get('user_branch')
    )
    service = UserService(raw_config,uow)
    with uow:
        user = service.create(actor=user,cmd=command)
    await callback.message.answer(f'Пользователь: {formatter.user_formatter(user)} был добавлен')
