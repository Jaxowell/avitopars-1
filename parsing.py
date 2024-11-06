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
            # Открываем браузер и контекст один раз
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(user_agent="Mozilla/5.0 ... Chrome/100.0.4896.60 Safari/537.36")
            await context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media", "other"] else route.continue_())

            while True:
                # Проверка флага is_running
                user_data = self.database.load_user_state(user_id)
                if not user_data.get(user_id, {}).get('is_running'):
                    self.logger.info(f"Парсер для пользователя {user_id} остановлен.")
                    break

                if user_id in user_data and user_data[user_id]['url']:
                    url = user_data[user_id]['url']
                    self.logger.info(f"Начинаем парсинг для пользователя {user_id} по URL: {url}")

                    # Создаём новую вкладку и загружаем страницу
                    page = await context.new_page()
                    try:
                        # Используем "domcontentloaded" для быстрой загрузки HTML, но не дожидаемся полной загрузки
                        await page.goto(url, wait_until="domcontentloaded")
                        
                        # Ожидаем нужный элемент (например, контейнер объявлений)
                        await page.wait_for_selector('div[data-marker="item"]', timeout=10000)
                        self.logger.info("Элемент объявлений найден.")

                        # Выполняем парсинг
                        all_ads = await page.query_selector_all('div[data-marker="item"]')
                        self.logger.info(f"Найдено объявлений: {len(all_ads)}")

                        # Логика обработки объявлений
                        for ad in reversed(all_ads[:20]):
                            ad_id = await ad.get_attribute('data-item-id')
                            if ad_id and not self.database.is_ad_seen(user_id, ad_id):
                                # Обработка новых объявлений
                                link = await ad.query_selector('a')
                                if link:
                                    ad_link = await link.get_attribute('href')
                                    full_link = f"https://www.avito.ru{ad_link}"
                                    await bot.send_message(chat_id=user_id, text=f"Новое объявление: {full_link}")

                        # Обновляем базу данных
                        self.database.replace_oldest_ads(user_id, [await ad.get_attribute('data-item-id') for ad in all_ads[:20]])

                        await asyncio.sleep(15)
                    except Error as e:
                        self.logger.error(f"Ошибка при парсинге: {e}")
                    finally:
                        await page.close()  # Закрываем только вкладку
                else:
                    await asyncio.sleep(10)