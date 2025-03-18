from __future__ import annotations

import asyncio
import os

from llm import get_response
from logger_config import logger
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InputFile
from voice import convert_speech_to_text, convert_text_to_speech

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
        "video",
        "document",
        "location",
        "contact",
        "sticker",
    ],
)
async def handle_not_supported(message):
    info_msg = "I can only process text and voice messages for now."
    await bot.reply_to(message, info_msg)
    logger.info(f"User {message.chat.id} sent a non-text message.")


@bot.message_handler(content_types=["voice"])
async def handle_voice(message):
    await bot.send_chat_action(message.chat.id, "typing")
    file_info = await bot.get_file(message.voice.file_id)
    file_path = file_info.file_path
    f_name = f"temp/{message.chat.id}.ogg"
    with open(f_name, "wb") as file:
        file.write(await bot.download_file(file_path))

    logger.debug(
        f"Downloaded voice message from user {message.chat.id} to {f_name}"
    )

    response = get_response(convert_speech_to_text(f_name))

    await bot.reply_to(message, response)
    logger.info(f"Dr. Ellis replied to user {message.chat.id}: {response}")

    await bot.send_chat_action(message.chat.id, "record_voice")
    convert_text_to_speech(response)
    await bot.send_voice(
        chat_id=message.chat.id, voice=InputFile("out_voice.ogg")
    )
    logger.info(f"Dr. Ellis replied with voice to user {message.chat.id}.")


@bot.message_handler(content_types=["text"])
async def handle_text(message):
    logger.info(f"User {message.chat.id} sent a message: {message.text}")
    response = get_response(message.text)
    await bot.reply_to(message, response)
    logger.info(f"Dr. Ellis replied to user {message.chat.id}: {response}")

    convert_text_to_speech(response)
    await bot.send_voice(
        chat_id=message.chat.id, voice=InputFile("output.ogg")
    )
    logger.info(f"Dr. Ellis replied with voice to user {message.chat.id}.")


def start_polling():
    asyncio.run(bot.polling())
    logger.info("Dr. Ellis is starting to poll messages.")


if __name__ == "__main__":
    start_polling()
