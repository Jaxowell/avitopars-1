from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import types



async def menu(message: types.Message):
    # Создаем reply-клавиатуру с кнопками
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Опции'), KeyboardButton(text='Помощь'), KeyboardButton(text='кто нажмёт тот здохнет')]  # Кнопки, которые будут отображаться
        ],
        resize_keyboard=True  # Для уменьшения размера клавиатуры
    )

    # Отправляем сообщение с этой клавиатурой
    await message.answer("Добро пожаловать! Выберите одну из опций:", reply_markup=reply_keyboard)


async def handle_help(message: types.Message):
    await message.answer("Вот некоторые команды, которые могут вам помочь:\n"
                         "/start - начать работу с ботом\n"
                         "/stop - остановить парсинг\n"
                         "/set_url <ссылка> - установить URL для парсинга.")


async def handle_contacts(message: types.Message):
    await message.answer("Контанты разработчиков:\n"
                         "@vbudke9999 - Даниил.\n"
                         "@jaxowell - Данила.\n"
                         "@Krikozyabra - Влад.")