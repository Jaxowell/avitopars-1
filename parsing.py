import asyncio
import logging
from db import Database
from aiogram import Bot
from playwright.async_api import async_playwright, Error, TimeoutError

class Parser:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.database = Database(logger)
        
    async def start_parsing(self, user_id, bot: Bot):
        asyncio.create_task(self.parse_avito(user_id, bot))
        
    async def parse_avito(self, user_id, bot: Bot):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            while True:
                user_data = self.database.load_user_state(user_id)
                if user_id in user_data and user_data[user_id]['is_running'] and user_data[user_id]['url']:
                    url = user_data[user_id]['url']
                    self.logger.info(f"Начинаем парсинг для пользователя {user_id} по URL: {url}")
                    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36")
                    page = await context.new_page()
                    try:
                        self.logger.info(f"Переход на страницу: {url}")
                        await page.goto(url, timeout=60000)  # Увеличиваем таймаут
                        self.logger.info("Страница успешно загружена.")
                        await asyncio.sleep(3)
                        await page.wait_for_selector('div[data-marker="item"]', timeout=60000)
                        all_ads = await page.query_selector_all('div[data-marker="item"]')
                        self.logger.info(f"Найдено объявлений: {len(all_ads)}")
                        
                        if not all_ads:
                            self.logger.warning("Объявления не найдены, повторная проверка через 15 секунд.")
                            await asyncio.sleep(15)
                            await page.close()
                            continue
                        
                        ads = all_ads[:20]

                        for ad in reversed(ads):
                            ad_id = await ad.get_attribute('data-item-id')
                            if ad_id:
                                self.logger.info(f"Получен ID объявления: {ad_id}")
                                if not self.database.is_ad_seen(user_id, ad_id):
                                    self.database.add_ad_id(user_id, ad_id)  # Проверьте, что user_id здесь не None
                                    link = await ad.query_selector('a')
                                    if link:
                                        ad_link = await link.get_attribute('href')
                                        full_link = f"https://www.avito.ru{ad_link}"
                                        self.logger.info(f"Отправка объявления: {full_link} для пользователя {user_id}")
                                        await bot.send_message(chat_id=user_id, text=f"Новое объявление: {full_link}")
                            else:
                                self.logger.warning("Не удалось получить ID объявления")

                        await asyncio.sleep(15)
                    except Error as e:
                        self.logger.error(f"Ошибка при парсинге: {e}")
                        await asyncio.sleep(10)
                    finally:
                        await page.close()
                else:
                    await asyncio.sleep(10)