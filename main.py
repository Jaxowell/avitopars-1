import asyncio
import sqlite3
from playwright.async_api import async_playwright, Error, TimeoutError
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '7245987986:AAHZ4Kq7AX214yZADs18trFGybQ5iVxWvQQ'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создание базы данных или подключение к существующей
conn = sqlite3.connect('ads.db')
conn.isolation_level = None  # Автокоммит включён
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS ads (user_id INTEGER NOT NULL, ad_id TEXT, PRIMARY KEY (user_id, ad_id))")
cursor.execute("CREATE TABLE IF NOT EXISTS user_urls (user_id INTEGER PRIMARY KEY, url TEXT)")
conn.commit()

# Словарь для хранения данных пользователей (URL, состояние парсинга)
user_data = {}

async def start_parsing(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} запускает парсер.")
    # Проверяем, установлен ли URL для пользователя
    cursor.execute("SELECT url FROM user_urls WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        url = result[0]
        user_data[user_id] = {'is_running': True, 'url': url}
        await message.reply("Парсер запущен.")
        asyncio.create_task(parse_avito(user_id))  # Запуск парсера здесь
    else:
        await message.reply("URL не установлен. Пожалуйста, установите URL с помощью /set_url <ссылка>")

async def stop_parsing(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data or not user_data[user_id]['is_running']:
        await message.reply("Парсер уже остановлен.")
    else:
        user_data[user_id]['is_running'] = False
        await message.reply("Парсер остановлен.")

async def set_url(message: types.Message):
    user_id = message.from_user.id
    if len(message.text.split()) > 1:
        url = message.text.split(' ', 1)[1]
        # Сохранение URL в таблице user_urls
        cursor.execute("REPLACE INTO user_urls (user_id, url) VALUES (?, ?)", (user_id, url))
        conn.commit()
        # Очистка базы данных объявлений для пользователя при новом URL
        cursor.execute("DELETE FROM ads WHERE user_id = ?", (user_id,))
        conn.commit()
        await message.reply(f"Установлена новая ссылка для парсинга: {url}")
        # Обновляем URL в user_data, если парсинг уже запущен
        if user_id in user_data:
            user_data[user_id]['url'] = url
        else:
            user_data[user_id] = {'is_running': False, 'url': url}
    else:
        await message.reply("Ошибка: ссылка не предоставлена. Используйте: /set_url <ссылка>")

def is_ad_seen(user_id, ad_id):
    cursor.execute("SELECT 1 FROM ads WHERE user_id = ? AND ad_id = ?", (user_id, ad_id))
    return cursor.fetchone() is not None

def add_ad_id(user_id, ad_id):
    try:
        logger.info(f"Добавление ID объявления {ad_id} для пользователя {user_id}")
        cursor.execute("INSERT INTO ads (user_id, ad_id) VALUES (?, ?)", (user_id, ad_id))
        conn.commit()
        logger.info(f"Успешно добавлен ID объявления {ad_id} для пользователя {user_id}")
    except sqlite3.IntegrityError as e:
        logger.warning(f"ID объявления {ad_id} для пользователя {user_id} уже существует: {e}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении ID {ad_id} для пользователя {user_id}: {e}")

async def parse_avito(user_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        while True:
            if user_id in user_data and user_data[user_id]['is_running'] and user_data[user_id]['url']:
                url = user_data[user_id]['url']
                logger.info(f"Начинаем парсинг для пользователя {user_id} по URL: {url}")
                context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36")
                page = await context.new_page()
                try:
                    logger.info(f"Переход на страницу: {url}")
                    await page.goto(url, timeout=60000)  # Увеличиваем таймаут
                    logger.info("Страница успешно загружена.")
                    await asyncio.sleep(3)

                    await page.wait_for_selector('div[data-marker="item"]', timeout=60000)
                    all_ads = await page.query_selector_all('div[data-marker="item"]')
                    logger.info(f"Найдено объявлений: {len(all_ads)}")
                    
                    if not all_ads:
                        logger.warning("Объявления не найдены, повторная проверка через 15 секунд.")
                        await asyncio.sleep(15)
                        await page.close()
                        continue
                    
                    ads = all_ads[:20]

                    for ad in reversed(ads):
                        ad_id = await ad.get_attribute('data-item-id')
                        if ad_id:
                            logger.info(f"Получен ID объявления: {ad_id}")
                            if not is_ad_seen(user_id, ad_id):
                                add_ad_id(user_id, ad_id)  # Проверьте, что user_id здесь не None
                                link = await ad.query_selector('a')
                                if link:
                                    ad_link = await link.get_attribute('href')
                                    full_link = f"https://www.avito.ru{ad_link}"
                                    logger.info(f"Отправка объявления: {full_link} для пользователя {user_id}")
                                    await bot.send_message(chat_id=user_id, text=f"Новое объявление: {full_link}")
                        else:
                            logger.warning("Не удалось получить ID объявления")

                    await asyncio.sleep(15)
                except Error as e:
                    logger.error(f"Ошибка при парсинге: {e}")
                    await asyncio.sleep(10)
                finally:
                    await page.close()
            else:
                await asyncio.sleep(10)


async def main():
    dp.message.register(start_parsing, Command(commands=['start']))
    dp.message.register(stop_parsing, Command(commands=['stop']))
    dp.message.register(set_url, Command(commands=['set_url']))

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())