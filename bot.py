from db import Database
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import ConfigParser
from parsing import Parser
import logging
from buttons import *
import re

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

    @staticmethod
    async def help_button_handler(message: types.Message):
        await handle_help(message)

    async def start_parsing(self, message: types.Message):
        user_id = message.from_user.id
        self.logger.info(f"Пользователь {user_id} пытается запустить парсинг.")

        if not self.database.is_authorized(user_id):
            await message.reply("Вы не авторизованы. Пожалуйста, нажмите 'АВТОРИЗАЦИЯ' для продолжения.")
            return

        result = self.database.load_url(user_id)
        if result:
            url = result[0]
            self.database.save_user_state(user_id, url, True)
            await message.reply("Парсер запущен. Ожидайте новые объявления.")
            await show_parsing_menu(message, is_running=True)  # Обновляем меню с кнопкой остановки
            try:
                await self.parser.start_parsing(user_id, self.bot)
            except Exception as e:
                self.logger.error(f"Ошибка запуска парсера: {e}")
                await message.reply("Ошибка при запуске парсинга.")
        else:
            await message.reply("Ошибка: URL для парсинга не установлен. Используйте команду /set_url <ссылка>.")

    async def start_greeting(self, message: types.Message):
        user_id = message.from_user.id
        self.logger.info(f"Пользователь {user_id} запустил команду /start.")
        if not self.database.is_authorized(user_id):
            await show_start_menu(message)
        else:
            await message.reply(f"С возвращением, {message.from_user.username}!")
            await show_autorized_menu(message)

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
        user_state = self.database.load_user_state(user_id)

        if user_id not in user_state or not user_state[user_id]['is_running']:
            await message.reply("Парсер уже остановлен.")
        else:
            self.database.save_user_state_running(user_id, False)
            await message.reply("Парсер остановлен.")
            await self.parser.stop_parsing(user_id)  # Завершаем парсинг
            await show_parsing_menu(message, is_running=False)  # Обновляем меню с кнопкой запуска

    async def handle_url_action(self, message: types.Message):
        user_id = message.from_user.id
        text = message.text.strip()

        if text == "В главное меню":
            # Переход в главное меню
            self.logger.info(f"Пользователь {user_id} нажал 'В главное меню'.")
            self.database.reset_user_menu_state(user_id)  # Сбрасываем состояние меню
            await show_parsing_menu(message, is_running=False)  # Отображаем главное меню
            return

        # Получаем список URL
        urls = self.database.get_user_urls(user_id)

        # Проверяем, выбрал ли пользователь конкретный URL
        selected_url = next((url for url, name in urls if name == text), None)
        if selected_url:
            self.logger.info(f"Пользователь {user_id} выбрал URL для управления: {text}")
            await self.show_url_management_menu(message, text, selected_url)
            return

        # Если ничего не найдено, отправляем сообщение об ошибке
        self.logger.warning(f"Пользователь {user_id} ввёл неизвестную команду: {text}")
        await message.reply("Не удалось найти выбранный URL. Попробуйте снова.")

    async def handle_selected_url(self, message: types.Message):
        user_id = message.from_user.id
        selected_url_name = message.text.strip()

        # Получаем URL по выбранному названию
        urls = self.database.get_user_urls(user_id)
        selected_url = next((url for url, name in urls if name == selected_url_name), None)

        if selected_url:
            # Отображаем меню для выбранного URL
            await self.show_url_management_menu(message, selected_url_name, selected_url)
        else:
            await message.reply("Не удалось найти выбранный URL.")

    async def handle_url_management_action(self, message: types.Message):
        user_id = message.from_user.id
        text = message.text.strip()

        if text == "Назад":
            # Возвращаемся в меню настроек URL
            self.database.save_user_state_menu(user_id, in_url_menu=True)  # Сохраняем, что пользователь возвращается
            await self.configure_urls(message)
            return

        # Запуск парсинга
        if text.startswith("Запустить парсинг для"):
            url_name = text.replace("Запустить парсинг для ", "")
            await message.reply(f"Запуск парсинга для {url_name}...")

        # Остановка парсинга
        elif text.startswith("Остановить парсинг для"):
            url_name = text.replace("Остановить парсинг для ", "")
            await message.reply(f"Остановка парсинга для {url_name}...")

        # Удаление URL
        elif text.startswith("Удалить URL:"):
            url_name = text.replace("Удалить URL: ", "")
            self.database.delete_url(user_id, url_name)
            await message.reply(f"Удаление URL {url_name} завершено.")
            await self.configure_urls(message)

    async def send_msg(self, user_id, text):
        self.bot.send_message(chat_id=user_id, text=text)

    async def go_back(self, message: types.Message):
        user_id = message.from_user.id
        user_state = self.database.load_user_state(user_id)
        self.logger.info(f"Состояние пользователя {user_id} при нажатии Назад: {user_state}")

        if user_state.get(user_id, {}).get('in_url_menu', False):
            self.logger.info(f"Возврат пользователя {user_id} в меню настроек URL.")
            await self.configure_urls(message)
        else:
            self.logger.info(f"Возврат пользователя {user_id} в главное меню.")
            await show_parsing_menu(message, is_running=False)

    async def register_commands(self):
        self.dp.message.register(self.start_greeting, Command(commands=['start']))
        self.dp.message.register(self.start_parsing, lambda message: message.text in ["Запустить парсинг", "Остановить парсинг"])
        self.dp.message.register(self.stop_parsing, Command(commands=['stop']))
        self.dp.message.register(self.set_url, Command(commands=['set_url']))
        self.dp.message.register(self.handle_authorization, lambda message: message.text == "АВТОРИЗАЦИЯ")
        self.dp.message.register(self.contacts_button_handler, lambda message: message.text == "Credits")
        self.dp.message.register(self.contacts_button_handler, lambda message: message.text == "кто нажмёт тот здохнет")
        self.dp.message.register(self.configure_urls, lambda message: message.text == 'Настроить URL')
        self.dp.message.register(self.handle_url_action, lambda message: message.text not in ["Назад", "В главное меню"])
        self.dp.message.register(self.handle_url_management_action, lambda message: message.text.startswith(("Запустить парсинг", "Остановить парсинг", "Удалить URL")))
        self.dp.message.register(self.handle_url_action, lambda message: message.text in ["В главное меню"])
        self.dp.message.register(self.handle_url_management_action, lambda message: message.text in ["Назад"])

    async def configure_urls(self, message: types.Message):
        user_id = message.from_user.id
        self.logger.info(f"Пользователь {user_id} открыл меню настроек URL.")
        self.database.save_user_state_menu(user_id, in_url_menu=True)  # Сохраняем состояние

        urls = self.database.get_user_urls(user_id)

        if not urls:
            await message.reply("У вас нет настроенных URL. Добавьте их с помощью команды /set_url \"<название>\" <URL>.")
            return

        # Кнопки: список URL + В главное меню
        keyboard = [[KeyboardButton(text=name)] for _, name in urls]
        keyboard.append([KeyboardButton(text="В главное меню")])  # Кнопка для выхода в главное меню

        reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        await message.answer("Выберите URL для управления или вернитесь в главное меню:", reply_markup=reply_markup)

    async def show_url_management_menu(self, message: types.Message, url_name: str, url: str):
        user_id = message.from_user.id
        self.logger.info(f"Пользователь {user_id} открыл управление для URL: {url_name}")
        self.database.save_user_state_menu(user_id, in_url_menu=False)  # Сохраняем, что пользователь сейчас в меню управления URL

        keyboard = [
            [KeyboardButton(text=f"Запустить парсинг для {url_name}")],
            [KeyboardButton(text=f"Остановить парсинг для {url_name}")],
            [KeyboardButton(text=f"Удалить URL: {url_name}")],
            [KeyboardButton(text="Назад")]  # Кнопка возврата в настройки URL
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        await message.answer(f"Управление для URL: {url_name} ({url}):", reply_markup=reply_markup)

    async def set_url(self, message: types.Message):
        user_id = message.from_user.id
        text = message.text.strip()

        # Используем регулярное выражение для извлечения названия и URL
        match = re.match(r'/set_url\s+"([^"]+)"\s+(.+)', text)

        if match:
            name = match.group(1)  # Название в кавычках
            url = match.group(2)   # URL после названия
            try:
                self.database.save_url(user_id, url, name)
                await message.reply(f"Добавлен новый URL с названием '{name}' и URL: {url}.")
            except ValueError as e:
                await message.reply(str(e))
        else:
            await message.reply("Используйте: /set_url \"<название>\" <URL>")


    async def start_bot(self):
        await self.register_commands()
        await self.dp.start_polling(self.bot)