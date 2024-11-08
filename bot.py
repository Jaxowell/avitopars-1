from db import Database
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import ConfigParser
from parsing import Parser
import logging
from buttons import show_authorization_success, handle_help, handle_contacts, already_authorized, show_start_menu, show_autorized_menu


class MainBot:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.cfgParser = ConfigParser(logger)
        self.bot = Bot(token=self.cfgParser.get_token())
        self.dp = Dispatcher()
        self.database = Database(logger)
        self.parser = Parser(logger)

    @staticmethod
    async def contacts_button_handler(message: types.Message):
        await handle_contacts(message)

    async def help_button_handler(self, message: types.Message):
        await handle_help(message)

    async def start_parsing(self, message: types.Message):
        user_id = message.from_user.id
        self.logger.info(f"Пользователь {user_id} запускает бота.")
        await show_start_menu(message)
        result = self.database.load_url(user_id)
        if result:
            url = result[0]
            self.database.save_user_state(user_id, url, True)
            await message.reply("Парсер запущен.")
            await self.parser.start_parsing(user_id, self.bot)# Запуск парсера здесь

    async def handle_authorization(self, message: types.Message):
        user_id = message.from_user.id
        if not self.database.is_authorized(user_id):
            self.database.authorize_user(user_id)
            await show_authorization_success(message, message.from_user.username)
            await asyncio.sleep(0.1)
            await show_autorized_menu(message)
        else:
            await already_authorized(message, message.from_user.username)
            await asyncio.sleep(0.1)
            await show_autorized_menu(message)

    async def stop_parsing(self, message: types.Message):
        user_id = message.from_user.id
        user_state = self.database.load_user_state()  # Исправлено: добавлены скобки для вызова метода
        if user_id not in user_state or not user_state[user_id]['is_running']:
            await message.reply("Парсер уже остановлен.")
        else:
            self.database.save_user_state_running(user_id, False)
            await message.reply("Парсер остановлен.")

    async def set_url(self, message: types.Message):
        user_id = message.from_user.id
        if len(message.text.split()) > 1:
            url = message.text.split(' ', 1)[1]
            # Сохранение URL в таблице user_urls
            self.database.save_url(user_id, url)
            # Очистка базы данных объявлений для пользователя при новом URL
            self.database.del_urls_from_ads(user_id)
            await message.reply(f"Установлена новая ссылка для парсинга: {url}")
            # Обновляем URL в user_data, если парсинг уже запущен
            user_states = self.database.load_user_state()  # Обратите внимание на вызов метода
            if user_id in user_states:
                self.database.save_user_state_url(user_id, url)
            else:
                self.database.save_user_state(user_id, url, False)
        else:
            await message.reply("Ошибка: ссылка не предоставлена. Используйте: /set_url <ссылка>")

    async def send_msg(self, user_id, text):
        self.bot.send_message(chat_id=user_id, text=text)

    async def register_commands(self):
        self.dp.message.register(self.start_parsing, Command(commands=['start']))
        self.dp.message.register(self.stop_parsing, Command(commands=['stop']))
        self.dp.message.register(self.set_url, Command(commands=['set_url']))
        self.dp.message.register(self.handle_authorization, lambda message: message.text == "АВТОРИЗАЦИЯ")
        self.dp.message.register(self.help_button_handler, lambda message: message.text == "Помощь")
        self.dp.message.register(self.contacts_button_handler, lambda message: message.text == "кто нажмёт тот здохнет")

    async def start_bot(self):
        await self.register_commands()
        await self.dp.start_polling(self.bot)