import aiogram
from aiogram import types
from dotenv import load_dotenv
from os import getenv
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

import handlers.keyboards as kb

load_dotenv()  # читает .env из CWD

TOKEN = getenv("BOT_TOKEN")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(message: types.Message):
        await message.answer("Управление реле", reply_markup="")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())