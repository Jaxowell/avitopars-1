from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from messages import *
import db

start_router = Router()


@start_router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if not db.is_authorized(user_id=user_id):
        await show_start_menu(message)
    else:
        await message.reply(f"С возвращением, {message.from_user.username}!")
        if db.get_parsing_status(user_id=user_id) == 3:
            db.set_parsing_status(user_id=user_id, parsing=False)
        await show_mainmenu(message)


@start_router.message(F.text == "АВТОРИЗАЦИЯ")
async def auth(message: Message):
    user_id = message.from_user.id
    db.authorize_user(user_id=user_id)
    db.set_parsing_status(user_id=user_id, parsing=False)
    await show_mainmenu(message)
    await message.answer("Приятного пользования нашим продуктом!")


async def show_start_menu(message: types.Message):
    auth_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="АВТОРИЗАЦИЯ")]], resize_keyboard=True
    )
    await message.answer(
        "Добро пожаловать! Нажмите 'АВТОРИЗАЦИЯ' для доступа.",
        reply_markup=auth_keyboard,
    )
