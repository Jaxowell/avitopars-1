from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import types


async def show_start_menu(message: types.Message):
    auth_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="АВТОРИЗАЦИЯ")]],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать! Нажмите 'АВТОРИЗАЦИЯ' для доступа.", reply_markup=auth_keyboard)


async def show_autorized_menu(message: types.Message):
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Опции'), KeyboardButton(text='Помощь')],
            [KeyboardButton(text='кто нажмёт тот здохнет')]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите одну из опций...", reply_markup=reply_keyboard)


async def show_authorization_success(message: types.Message, user_id: str):
    await message.answer(f"Вы успешно авторизованы, {user_id}!", reply_markup=ReplyKeyboardRemove())


async def already_authorized(message: types.Message, user_id: str):
    await message.answer(f"Добро пожаловать, {user_id}!", reply_markup=ReplyKeyboardRemove())


async def handle_help(message: types.Message):
    await message.answer("Вот некоторые команды, которые могут вам помочь:\n"
                         "/start - начать работу с ботом\n"
                         "/parsing - запустить парсинг\n"
                         "/stop - остановить парсинг\n"
                         "/set_url <ссылка> - установить URL для парсинга.")


async def handle_contacts(message: types.Message):
    await message.answer("Контакты разработчиков:\n"
                         "@vbudke9999 - Даниил\n"
                         "@jaxowell - Данила\n"
                         "@Krikozyabra - Влад")
