import asyncio
import os
from logger_config import logger
from dotenv import load_dotenv
from groq import Groq, APIError
from telebot.async_telebot import AsyncTeleBot

load_dotenv()


bot = AsyncTeleBot(os.getenv('BOT_TOKEN'))
client = Groq(api_key=os.environ['GROQ_API_KEY'])


def get_response(message):
    logger.info(f"Sending message to Groq API: {message}")
    try:
        chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                model='llama3-70b-8192'
            )
        response = chat_completion.choices[0].message.content
        logger.info(f"Received response from Groq API: {response}")
        return response

    except APIError as e:
        error_messages = {
            400: "Invalid request. Please check your input.",
            401: "Unauthorized. Check Groq API key.",
            404: "Model not found. Verify the model name.",
            429: "Rate limit exceeded. Try again later.",
            500: "Internal server error. Try again later."
        }
        logger.error(f"API error: {e}")
        return error_messages.get(e.status_code, f"API error: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"


@bot.message_handler(commands=['start'])
async def start(message):
    greeting_msg = 'Hello, I am Dr. Ellis. How can I help you today?'
    await bot.send_message(message.chat.id, greeting_msg)
    logger.info(f"User {message.chat.id} started a conversation.")


@bot.message_handler(func=lambda message: True, content_types=[
    'audio', 'photo', 'voice', 'video', 'document',
    'location', 'contact', 'sticker'
])
async def handle_non_text(message):
    info_msg = 'I can only process text messages for now.'
    await bot.reply_to(message, info_msg)
    logger.info(f"User {message.chat.id} sent a non-text message.")


@bot.message_handler()
async def handle_text(message):
    logger.info(f"User {message.chat.id} sent a message: {message.text}")
    response = get_response(message.text)
    await bot.reply_to(message, response)
    logger.info(f"Dr. Ellis replied to user {message.chat.id}: {response}")

asyncio.run(bot.polling())
