import asyncio
from bot import MainBot
from logger import Log

if __name__ == '__main__':
    logger = Log()
    tgBot = MainBot(logger.getLogger())
    asyncio.run(tgBot.start_bot())