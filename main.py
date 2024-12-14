import asyncio
from bot import MainBot

if __name__ == "__main__":
    tgBot = MainBot()
    asyncio.run(tgBot.start_bot())
