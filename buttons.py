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
            [KeyboardButton(text='Запустить парсинг')],
            [KeyboardButton(text='Настроить URL')],
            [KeyboardButton(text='Помощь')],
            [KeyboardButton(text='Credits')]
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

async def show_parsing_menu(message: types.Message, is_running: bool):
    keyboard = []

    # Если парсинг запущен, показываем кнопку для его остановки
    if is_running:
        keyboard.append([KeyboardButton(text='Остановить парсинг')])
    else:
        keyboard.append([KeyboardButton(text='Запустить парсинг')])

    # Добавляем другие кнопки
    keyboard.append([KeyboardButton(text='Настроить URL')])
    keyboard.append([KeyboardButton(text='Помощь')])
    keyboard.append([KeyboardButton(text='Credits')])

    # Добавляем кнопку "Назад"
    keyboard.append([KeyboardButton(text="Назад")])

    reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    await message.answer("Выберите опцию:", reply_markup=reply_markup)

async def show_url_menu(message: types.Message, urls: list):
    # Создаем список списков для клавиатуры
    keyboard = []

    # Добавляем кнопки для каждого URL
    for url, name in urls:
        keyboard.append([KeyboardButton(text=f"Остановить: {name}"), KeyboardButton(text=f"Запустить: {name}")])
        keyboard.append([KeyboardButton(text=f"Удалить: {name}")])

    # Добавляем кнопку для возврата
    keyboard.append([KeyboardButton(text="Назад")])

    # Создаем объект клавиатуры с заполненным полем `keyboard`
    reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    await message.answer("Управление URL:", reply_markup=reply_markup)

async def show_url_management_menu(message: types.Message, url_name: str, url: str):
    keyboard = [
        [KeyboardButton(text=f"Запустить парсинг для {url_name}")],
        [KeyboardButton(text=f"Остановить парсинг для {url_name}")],
        [KeyboardButton(text=f"Удалить URL: {url_name}")],
        [KeyboardButton(text="Назад")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    await message.answer(f"Управление для URL: {url_name} ({url}):", reply_markup=reply_markup)


async def handle_contacts(message: types.Message):
    await message.answer("Контакты разработчиков:\n"
                         "@vbudke9999 - Даниил\n"
                         "@jaxowell - Данила\n"
                         "@Krikozyabra - Влад")