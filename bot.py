from db import Database
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import ConfigParser
from parsing import Parser
import logging

class MainBot:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.cfgParser = ConfigParser(logger)
        self.bot = Bot(token=self.cfgParser.get_token())
        self.dp = Dispatcher()
        self.database = Database(logger)
        self.parser = Parser(logger)
        
    async def start_parsing(self, message: types.Message):
        user_id = message.from_user.id
        self.logger.info(f"Пользователь {user_id} запускает парсер.")
        result = self.database.load_url(user_id)
        if result:
            url = result[0]
            self.database.save_user_state(user_id, url, True)
            await message.reply("Парсер запущен.")
            await self.parser.start_parsing(user_id, self.bot)# Запуск парсера здесь
        else:
            await message.reply("URL не установлен. Пожалуйста, установите URL с помощью /set_url <ссылка>")
            
    async def stop_parsing(self, message: types.Message):
        user_id = message.from_user.id
        if user_id not in self.database.load_user_state or not self.database.load_user_state[user_id]['is_running']:
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
            if user_id in self.database.load_user_state:
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
        
    async def start_bot(self):
        await self.register_commands()
        await self.dp.start_polling(self.bot)