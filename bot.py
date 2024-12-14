import asyncio
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from config import ConfigParser
from parsing import Parser
from handlers.start import start_router
from handlers.main_menu import main_menu_router, back_to_mainmenu, back_to_urlmenu
from handlers.url_settings import url_settings
from aiogram.fsm.storage.memory import MemoryStorage
from logger import Log
from messages import *

parsing_router = Router()
parser: Parser = None


def get_parser():
    global parser
    return parser


class MainBot:
    def __init__(self):
        global parser
        self.logger = Log().getLogger()
        self.cfgParser = ConfigParser(self.logger)
        self.bot = Bot(token=self.cfgParser.get_token())
        self.dp = Dispatcher(storage=MemoryStorage())
        parser = Parser(self.logger, self.bot)

    @parsing_router.message(F.text.startswith("Запустить парсинг"))
    async def start_parsing(message: types.Message):
        user_id = message.from_user.id

        if not db.is_authorized(user_id=user_id):
            await message.reply(
                "Вы не авторизованы. Пожалуйста, нажмите 'АВТОРИЗАЦИЯ' для продолжения."
            )
            return

        urls = db.get_urls_states(user_id=user_id)
        if len(urls) <= 0:
            db.set_parsing_status(user_id=user_id, parsing=True)
            await message.reply("Парсер запущен. Ожидайте новые объявления.")
            await back_to_mainmenu(message)
            try:
                await get_parser().start_parsing(user_id)
            except Exception as e:
                await message.reply("Ошибка при запуске парсинга.")
        else:
            await message.reply(
                "Ошибка: URL для парсинга не установлен (Используйте команду /set_url <ссылка>), либо ни одна из ссылка не отслеживается (Проверьте настройки ссылок)."
            )

    @parsing_router.message(F.text == "Остановить парсинг")
    async def stop_parsing(message: types.Message):
        user_id = message.from_user.id
        if not db.get_parsing_status(user_id=user_id):
            await message.reply("Парсер уже остановлен.")
        else:
            db.set_parsing_status(user_id=user_id, parsing=False)
            await message.reply("Парсер остановлен.")
            await get_parser().stop_parsing(user_id)  # Завершаем парсинг
            await back_to_mainmenu(message)

    def get_bot(self):
        return self.bot

    async def start_bot(self):
        db.init_db(self.logger)
        self.dp.include_routers(
            start_router, main_menu_router, url_settings, parsing_router
        )
        await self.bot.delete_webhook(drop_pending_updates=True)
        # await self.register_commands()
        await self.dp.start_polling(self.bot)
