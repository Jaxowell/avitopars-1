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

# Переменные для хранения состояния
is_running = False

# Установка базы данных для хранения последних 20 объявлений и URL
conn = sqlite3.connect('ads.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS ads (ad_id TEXT PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

def save_url(url):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('avito_url', ?)", (url,))
    conn.commit()

def load_url():
    cursor.execute("SELECT value FROM settings WHERE key = 'avito_url'")
    result = cursor.fetchone()
    return result[0] if result else ""

def add_ad_id(ad_id):
    cursor.execute("INSERT OR REPLACE INTO ads (ad_id) VALUES (?)", (ad_id,))
    conn.commit()
    cursor.execute("DELETE FROM ads WHERE rowid NOT IN (SELECT rowid FROM ads ORDER BY rowid DESC LIMIT 20)")
    conn.commit()

def is_ad_seen(ad_id):
    cursor.execute("SELECT 1 FROM ads WHERE ad_id = ?", (ad_id,))
    return cursor.fetchone() is not None

async def start_parsing(message: types.Message):
    global is_running, avito_url
    if is_running:
        await message.reply("Парсер уже запущен.")
    else:
        avito_url = load_url()
        if not avito_url:
            await message.reply("Ошибка: URL для парсинга не установлен. Используйте /set_url <ссылка> для установки.")
            return
        
        is_running = True
        asyncio.create_task(parse_avito(message.chat.id))
        await message.reply("Парсер запущен.")

async def stop_parsing(message: types.Message):
    global is_running
    if not is_running:
        await message.reply("Парсер уже остановлен.")
    else:
        is_running = False
        await message.reply("Парсер остановлен.")

async def set_url(message: types.Message):
    global avito_url
    avito_url = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else ""
    cursor.execute("DELETE FROM ads")
    conn.commit()
    if avito_url:
        save_url(avito_url)
        await message.reply(f"Установлена новая ссылка для парсинга: {avito_url}")
    else:
        await message.reply("Ошибка: ссылка не предоставлена. Используйте: /set_url <ссылка>")

async def parse_avito(chat_id):
    global is_running, avito_url
    async with async_playwright() as p:
        # Отключение headless для видимого интерфейса
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"
        )
        page = await context.new_page()

        while is_running:
            if avito_url:
                try:
                    logger.info(f"Открытие страницы: {avito_url}")
                    await page.goto(avito_url, timeout=60000)  # Увеличен таймаут до 60 секунд

                    await asyncio.sleep(3)

                    # Явное ожидание появления объявлений на странице
                    try:
                        await page.wait_for_selector('div[data-marker="item"]', timeout=20000)
                    except TimeoutError:
                        logger.warning("Элементы с 'data-marker=item' не загрузились в течение 20 секунд.")

                    all_ads = await page.query_selector_all('div[data-marker="item"]')
                    ads = all_ads[:20]  # Обрезка до первых 20 объявлений
                    logger.info(f"Найдено первых 20 объявлений: {len(ads)}")

                    # Отправляем только новые объявления
                    for ad in reversed(ads):  # Объявления снизу вверх
                        ad_id = await ad.get_attribute('data-item-id')
                        if ad_id and not is_ad_seen(ad_id):
                            add_ad_id(ad_id)
                            link = await ad.query_selector('a')
                            if link:
                                ad_link = await link.get_attribute('href')
                                full_link = f"https://www.avito.ru{ad_link}"
                                logger.info(f"Отправка объявления: {full_link}")
                                await bot.send_message(chat_id=chat_id, text=f"Новое объявление: {full_link}")
                        else:
                            logger.info(f"Объявление с ID {ad_id} уже обработано")

                    await asyncio.sleep(15)

                except Error as e:
                    logger.error(f"Ошибка при парсинге: {e}")
                    await asyncio.sleep(10)
            else:
                logger.warning("URL для парсинга не задан")
                await asyncio.sleep(10)

        await browser.close()

async def main():
    dp.message.register(start_parsing, Command(commands=['start']))
    dp.message.register(stop_parsing, Command(commands=['stop']))
    dp.message.register(set_url, Command(commands=['set_url']))

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())