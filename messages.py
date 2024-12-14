from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram import types

import db


async def show_mainmenu(message: types.Message):
    keyboard = []
    is_parsing = db.get_parsing_status(user_id=message.from_user.id)
    if not is_parsing:
        keyboard.append([KeyboardButton(text="Запустить парсинг")])
    else:
        keyboard.append([KeyboardButton(text="Остановить парсинг")])
    keyboard.append([KeyboardButton(text="Настроить URL")])
    keyboard.append([KeyboardButton(text="Помощь")])
    keyboard.append([KeyboardButton(text="Credits")])
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
    await message.answer("Выберите одну из опций...", reply_markup=reply_keyboard)


async def show_authorization_success(message: types.Message, user_id: str):

    await message.answer(
        f"Вы успешно авторизованы, {user_id}!", reply_markup=ReplyKeyboardRemove()
    )


async def already_authorized(message: types.Message, user_id: str):
    await message.answer(
        f"Добро пожаловать, {user_id}!", reply_markup=ReplyKeyboardRemove()
    )


async def show_url_management_menu(message: types.Message, url_name: str, url: str):
    await message.answer(
        "Управление для URL:" + url_name + " - " + url,
        reply_markup=ease_url_settings_list(message.from_user.id, url, url_name),
    )


def ease_url_settings_list(user_id: int, url: str, url_name: str):
    is_started = db.get_url_state(url=url, user_id=user_id)
    keyboard = [[KeyboardButton(text="Удалить ссылку - " + url_name)]]
    if not is_started:
        keyboard.append([KeyboardButton(text="Отслеживать - " + url_name)])
    else:
        keyboard.append([KeyboardButton(text="Не отслеживать - " + url_name)])
    keyboard.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard)


def ease_url_list(urls):
    # Кнопки: список URL + В главное меню
    keyboard = [[KeyboardButton(text="Настроить: " + name)] for _, name in urls]
    keyboard.append([KeyboardButton(text="В главное меню")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def show_url_list(message: types.Message, urls):
    await message.answer(
        "Выберите сайт, который хотите настроить:",
        reply_markup=ease_url_list(urls),
    )
