from __future__ import annotations

import asyncio
import os

from llm import get_response
from logger_config import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InputFile
from voice import create_audio

bot = AsyncTeleBot(os.getenv("BOT_TOKEN"))


@bot.message_handler(commands=["start"])
async def start(message):
    greeting_msg = "Hello, I am Dr. Ellis. How can I help you today?"
    await bot.send_message(message.chat.id, greeting_msg)
    logger.info(f"User {message.chat.id} started a conversation.")


@bot.message_handler(
    func=lambda message: True,
    content_types=[
        "audio",
        "photo",
        "voice",
        "video",
        "document",
        "location",
        "contact",
        "sticker",
    ],
)
async def handle_non_text(message):
    info_msg = "I can only process text messages for now."
    await bot.reply_to(message, info_msg)
    logger.info(f"User {message.chat.id} sent a non-text message.")


@bot.message_handler()
async def handle_text(message):
    logger.info(f"User {message.chat.id} sent a message: {message.text}")
    response = get_response(message.text)
    await bot.reply_to(message, response)
    logger.info(f"Dr. Ellis replied to user {message.chat.id}: {response}")

    create_audio(response)
    await bot.send_voice(
        chat_id=message.chat.id, voice=InputFile("output.ogg")
    )
    logger.info(f"Dr. Ellis replied with voice to user {message.chat.id}.")


def start_polling():
    asyncio.run(bot.polling())
    logger.info("Dr. Ellis is starting to poll messages.")
