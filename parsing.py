import asyncio
import logging

import db
from aiogram import Bot
from playwright.async_api import async_playwright, Error, TimeoutError


class Parser:
    def __init__(self, logger: logging.Logger, bot: Bot):
        self.bot = bot
        self.logger = logger
        self.browser = None
        self.context = None
        self.page = None  # Добавим переменную для страницы

    async def start_parsing(self, user_id):
        asyncio.create_task(self.parse_avito(user_id))

    async def stop_parsing(self, user_id):
        # Метод для завершения парсинга
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        self.logger.info(f"Парсинг для пользователя {user_id} остановлен.")

    async def parse_avito(self, user_id):
        async with async_playwright() as p:
            try:
                self.browser = await p.chromium.launch(headless=False)
                self.context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 ... Chrome/100.0.4896.60 Safari/537.36"
                )
                await self.context.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if route.request.resource_type
                        in ["image", "stylesheet", "font", "media", "other"]
                        else route.continue_()
                    ),
                )
                self.page = await self.context.new_page()

                while True:
                    user_status = db.get_parsing_status(user_id=user_id)
                    if not user_status:
                        self.logger.info(
                            f"Парсер для пользователя {user_id} остановлен."
                        )
                        break

                    urls = db.get_user_urls(user_id=user_id)
                    for el in urls:
                        url = el[0]
                        self.logger.info(
                            f"Начинаем парсинг для пользователя {user_id} по URL: {url}"
                        )

                        try:
                            await self.page.goto(url, wait_until="domcontentloaded")
                            await self.page.wait_for_selector(
                                'div[data-marker="item"]', timeout=10000
                            )

                            all_ads = await self.page.query_selector_all(
                                'div[data-marker="item"]'
                            )
                            self.logger.info(f"Найдено объявлений: {len(all_ads)}")

                            for ad in reversed(all_ads[:20]):
                                ad_id = await ad.get_attribute("data-item-id")
                                if ad_id and not db.is_ad_seen(
                                    user_id=user_id, ad_id=ad_id
                                ):
                                    link = await ad.query_selector("a")
                                    if link:
                                        ad_link = await link.get_attribute("href")
                                        full_link = f"https://www.avito.ru{ad_link}"
                                        await self.bot.send_message(
                                            chat_id=user_id,
                                            text=f"Новое объявление: {full_link}",
                                        )

                            # Сохраняем последние 20 объявлений
                            db.replace_oldest_ads(
                                user_id=user_id,
                                new_ad_ids=[
                                    await ad.get_attribute("data-item-id")
                                    for ad in all_ads[:20]
                                ],
                            )

                            # Пауза между итерациями
                            await asyncio.sleep(15)
                        except TimeoutError as e:
                            self.logger.warning(
                                f"Тайм-аут при парсинге для пользователя {user_id}: {e}"
                            )
                            await asyncio.sleep(10)
                        except Exception as e:
                            self.logger.error(
                                f"Ошибка при обработке объявлений для пользователя {user_id}: {e}"
                            )
                            await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(
                    f"Ошибка работы парсера для пользователя {user_id}: {e}"
                )

            finally:
                await self.page.close()
                await self.browser.close()
