from os import getenv
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from repository.create_migrations import run_migrations, create_migration_shema
from api.handlers import router as auth_router
from repository.unit_of_work import  main_factory_uow

load_dotenv()
dp = Dispatcher()



async def main():
    TOKEN = getenv("BOT_TOKEN")
    bot = Bot(token=TOKEN)
    with main_factory_uow() as uow:
        create_migration_shema(uow.con)
        run_migrations(uow.con)
    dp.include_router(auth_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
