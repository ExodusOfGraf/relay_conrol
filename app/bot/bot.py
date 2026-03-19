import aiogram
from dotenv import load_dotenv
from os import getenv
import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

load_dotenv()  # читает .env из CWD

TOKEN = getenv("BOT_TOKEN")
