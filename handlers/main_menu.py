from aiogram import Router, F
from aiogram.filters import Command
from messages import *
import db

main_menu_router = Router()


@main_menu_router.message(F.text == "Credits")
async def handle_contacts(message: types.Message):
    await message.answer(
        "Контакты разработчиков:\n"
        "@vbudke9999 - Даниил\n"
        "@jaxowell - Данила\n"
        "@Krikozyabra - Влад"
    )


@main_menu_router.message(F.text == "Помощь")
async def handle_help(message: types.Message):
    await message.answer(
        "Вот некоторые команды, которые могут вам помочь:\n"
        "/start - начать работу с ботом\n"
        "/start_parsing - запустить парсинг\n"
        "/stop_parsing - остановить парсинг\n"
        "/set_url 'имя' <ссылка> - установить URL для парсинга."
    )


@main_menu_router.message(F.text == "Настроить URL")
async def selectmenu_urls(message: types.Message):
    user_id = message.from_user.id
    # self.logger.info(f"Пользователь {user_id} открыл меню настроек URL.")
    db.save_user_state_menu(user_id=user_id, in_url_menu=True)  # Сохраняем состояние

    urls = db.get_user_urls(user_id=user_id)

    if not urls:
        await message.reply(
            'У вас нет URL для настройки. Добавьте их с помощью команды /set_url "<название>" <URL>.'
        )
        return

    await show_url_list(message, urls)


@main_menu_router.message(F.text == "В главное меню")
async def back_to_mainmenu(message: types.Message):
    await show_mainmenu(message)


@main_menu_router.message(F.text == "Назад")
async def back_to_urlmenu(message: types.Message):
    await selectmenu_urls(message)
