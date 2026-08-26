from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from core.schemas import CmdCreateAlert, CmdCreateTicket, QueryGetTicket
from bot.keyboards.main_keyboard import get_button_main
from bot.keyboards.ticket_keyboard import get_departments_menu, get_rule_menu, get_type_object, get_type_request, \
    get_manager_ticket_for_branch, get_specialist_from_depart
from bot.midleware import RequestContext
from core.enums import KindRule
from core.ticket_core import Rule

ticket_router = Router()

class TicketState(StatesGroup):
    waiting_depart = State()
    waiting_rule = State()
    routing_by_kind = State()
    waiting_severity = State()
    waiting_photo = State()
    create_alert = State()
    create_ticket = State()

@ticket_router.callback_query(F.data == 'create_ticket')
async def users_menu(callback: CallbackQuery,
                     ctx: RequestContext,
                     state: FSMContext):
    depart = ctx.uow.dep_mapper.get_all_depart()
    keyboard = get_departments_menu(ctx.formatter, depart)
    await state.set_state(TicketState.waiting_depart)
    await callback.message.edit_text(text='Выберите отдел: ', reply_markup=keyboard)

@ticket_router.callback_query(TicketState.waiting_depart)
async def depart_menu(callback: CallbackQuery,
                      ctx: RequestContext,
                      state: FSMContext):
    await callback.answer()
    dep_name, dep_id = callback.data.split(':')
    await state.update_data(depart_id=dep_id)
    await state.set_state(TicketState.waiting_rule)
    rules = ctx.uow.rule.get_rules({'target_id': dep_id})
    keyboard = get_rule_menu(ctx.formatter, rules)
    await callback.message.edit_text(f'{ctx.formatter.translate(dep_name)}:',
                                  reply_markup= keyboard)


@ticket_router.callback_query(TicketState.waiting_rule,F.data.startswith('class_rules'))
async def get_class_rule(callback: CallbackQuery,
                   ctx: RequestContext):
    await callback.answer()
    _, class_rule = callback.data.split(':')
    rules = ctx.uow.rule.get_rules({'class': class_rule})
    keyboard = get_rule_menu(ctx.formatter, rules)
    await callback.message.edit_text(f'{ctx.formatter.translate(class_rule)}:',
                                  reply_markup= keyboard)

@ticket_router.callback_query(TicketState.waiting_rule,F.data.startswith('rules'))
async def get_rule(callback: CallbackQuery,
                   ctx: RequestContext,
                    state: FSMContext):
    await callback.answer()
    _, code = callback.data.split(':')
    rule = ctx.uow.rule.get_rules({'code': code})[0]
    await state.update_data(rule=rule)
    await state.set_state(TicketState.routing_by_kind)

@ticket_router.callback_query(TicketState.routing_by_kind)
async def routing_by_kind(callback: CallbackQuery,
                       state: FSMContext,
                       ctx: RequestContext):
    await callback.answer()
    data = await state.get_data()
    rule = data.get('rule')
    if isinstance(rule, Rule):
        rule_name = ctx.formatter.translate(rule.name)
    else:
        raise ValueError

    if rule.kind == KindRule.ALERT:
        await state.set_state(TicketState.create_alert)
        await callback.message.edit_text('Введите комментарий')
    elif rule.kind == KindRule.REQUEST:
        menu = get_type_request(ctx.formatter)
        await callback.message.edit_text(
            text=f"Выберите срочность заявки: {rule_name}", reply_markup=menu)
        await state.set_state(TicketState.waiting_severity)
    else:
        menu = get_type_object(ctx.formatter)
        await callback.message.edit_text(
            text=f"Выберите степень поломки: {rule_name}",reply_markup=menu)
        await state.set_state(TicketState.waiting_severity)


@ticket_router.callback_query(TicketState.waiting_severity, F.data)
async def get_severity(callback: CallbackQuery,
                       state: FSMContext):
    await callback.answer()
    severity = callback.data
    await state.update_data(severity= severity)
    menu = get_button_main()
    await callback.message.edit_text(text='Сфотографируйте вашу проблему: ',reply_markup=menu)
    await state.set_state(TicketState.waiting_photo)

@ticket_router.message(TicketState.waiting_photo, F.photo)
async def get_photo(message: Message,
                    state:FSMContext):
    menu = get_button_main()
    photo = message.photo[-1]
    await state.update_data(file_id=photo.file_id)
    await message.answer(text='Напишите комментарий:', reply_markup=menu)
    await state.set_state(TicketState.create_ticket)

@ticket_router.message(TicketState.waiting_photo)
async def process_photo_invalid(message: Message):
    await message.answer(
        text="Пожалуйста, отправьте именно фотографию (как изображение, а не файл).")

@ticket_router.message(TicketState.create_alert)
async def create_alert(message: Message,
                       ctx: RequestContext,
                       state: FSMContext):
    comment = message.text
    data = await state.get_data()
    rule = data.get('rule')
    cmd = CmdCreateAlert(code_alert=rule.code,
                         comment=comment)
    alert, recipients = ctx.service_alert.create(cmd,ctx.actor)
    msg = ctx.formatter.alert_formatter(alert)
    menu = get_button_main()
    for users_id in recipients.get_user_api_id():
        try:
            await ctx.bot.send_message(chat_id=users_id, text=msg)
            print(f"Отправлен пользователю {users_id}, {msg}")
        except TelegramBadRequest:
            print(f"Не был отправлен пользователю {users_id}, {msg}")
    await message.answer("Заявка была создана и отправлена.", reply_markup=menu)
    await state.clear()


@ticket_router.message(TicketState.create_ticket)
async def create_ticket(message: Message,
                       ctx: RequestContext,
                       state: FSMContext):
    comment = message.text
    data = await state.get_data()
    rule = data.get('rule')
    photo_id = data.get('file_id', None)
    severity = data.get('severity')
    menu = get_button_main()
    cmd = CmdCreateTicket(code_rule=rule.code,
                          severity=severity,
                          comment=comment,
                          file_id=photo_id)
    view, recipients = ctx.service_ticket.create(ctx.actor,cmd)
    msg = ctx.formatter.ticket_formatter(view)
    for users_id in recipients.get_user_api_id():
        try:
            if view.ticket.context.file_id:
                await ctx.bot.send_photo(
                    chat_id=users_id, photo=view.ticket.context.file_id, caption=msg)
            else:
                await ctx.bot.send_message(chat_id=users_id, text=msg)
            print(f"Отправлен пользователю {users_id}, {msg}")
        except TelegramBadRequest:
            print(f"Не был отправлен пользователю {users_id}, {msg}")
    await message.answer(f"Заявка была создана  отправлена: \n{msg}", reply_markup=menu)
    await state.clear()


@ticket_router.callback_query(F.data == 'ticket_for_branch')
async def get_menu_manager_ticket(callback: CallbackQuery):
    menu = get_manager_ticket_for_branch()
    await callback.message.edit_text("Панель управления заявками", reply_markup=menu)


@ticket_router.callback_query(F.data.startswith == 'my_ticket')
async def get_state_ticket(callback:CallbackQuery,
                           ctx: RequestContext):
    ticket_state = callback.data.split(':')[1]
    ticket_state_id = ctx.uow.state_mapper.get_state_id(ticket_state)
    cmd =QueryGetTicket(state_id=ticket_state_id)
    ticket = ctx.service_ticket.get(ctx.actor, cmd)
    ...

@ticket_router.callback_query(F.data == 'ticket_from_depart')
async def get_menu_manager_ticket(callback: CallbackQuery):
    menu = get_specialist_from_depart()
    await callback.message.edit_text("Панель управления заявками", reply_markup=menu)
