from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from .main_menu import selectmenu_urls, show_url_management_menu
from parsing import Parser

import db

url_settings = Router()


@url_settings.message(F.text.startswith("Настроить: "))
async def configure_url(message: Message):
    url_name = message.text.replace("Настроить: ", "")
    url = db.get_url(user_id=message.from_user.id, url_name=url_name)
    await show_url_management_menu(message, url_name, url)


@url_settings.message(F.text.startswith("Удалить ссылку - "))
async def delete_url(message: Message):
    url_name = message.text.replace("Удалить ссылку - ", "")
    db.delete_url(user_id=message.from_user.id, url_name=url_name)
    await selectmenu_urls(message)


@url_settings.message(Command(commands=["set_url"]))
async def set_url(message: Message, command: CommandObject):
    args = command.args.strip().split(" ")
    if len(args) == 2:
        user_id = message.from_user.id
        name, url = args
        try:
            db.save_url(user_id=user_id, url=url, name=name)
            await message.reply(
                f"Добавлен новый URL с названием '{name}' и URL: {url}."
            )
        except ValueError as e:
            await message.reply(str(e))
    else:
        await message.reply("Используйте: /set_url <название> <URL>")


@url_settings.message(F.text.startswith("Не отслеживать - "))
async def set_parsingstatus_stop(message: Message):
    url_name = message.text.replace("Не отслеживать - ", "")
    url = db.get_url(user_id=message.from_user.id, url_name=url_name)
    db.save_user_state_running(user_id=message.from_user.id, is_running=False, url=url)
    await message.answer(f"Ссылка с именем {url_name} не будет отслеживаться")
    await selectmenu_urls(message)


@url_settings.message(F.text.startswith("Отслеживать - "))
async def set_parsingstatus_run(message: Message):
    url_name = message.text.replace("Отслеживать - ", "")
    url = db.get_url(user_id=message.from_user.id, url_name=url_name)
    db.save_user_state_running(user_id=message.from_user.id, is_running=True, url=url)
    await message.answer(f"Ссылка с именем {url_name} будет отслеживаться")
    await selectmenu_urls(message)
