import os

from dotenv import load_dotenv
from groq import Groq
from logger_config import logger

load_dotenv()


client = Groq(api_key=os.environ["GROQ_API_KEY"])


def get_response(message):
    logger.info(f"Sending message to Groq API: {message}")
    try:
        chat_completion = client.chat.completions.create(
            model="qwen-2.5-32b",
            messages=[{"role": "user", "content": message}],
        )
        response = chat_completion.choices[0].message.content
        logger.info(f"Received response from Groq API: {response}")
        return response

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"
