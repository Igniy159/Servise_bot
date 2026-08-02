from os import getenv
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from api.midleware import AuthMiddleware
from core.loader import raw_config
from repository.create_migrations import run_migrations, create_migration_shema, DB_PATH
from api.handlers.main_handler import main_routers
from repository.unit_of_work import UowFactory

class FakeUser:
    employee = 333333
    manager = 111111
    specialist = 222222

async def main():
    dp = Dispatcher()
    bot = Bot(token=getenv("BOT_TOKEN"))
    main_factory_uow = UowFactory(DB_PATH)
    middleware_example = AuthMiddleware(main_factory_uow, raw_config, fake_user_id= FakeUser.employee)
    for router in main_routers:
        router.message.middleware(middleware_example)
        router.callback_query.middleware(middleware_example)
        dp.include_router(router)
    with main_factory_uow() as uow:
        create_migration_shema(uow.con)
        run_migrations(uow.con)
    await dp.start_polling(bot)

if __name__ == '__main__':
    load_dotenv()
    asyncio.run(main())
