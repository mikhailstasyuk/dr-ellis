from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, trim_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from logger_config import logger
from telebot.async_telebot import AsyncTeleBot

load_dotenv()


bot = AsyncTeleBot(os.getenv("BOT_TOKEN"))

model = init_chat_model("qwen-2.5-32b", model_provider="groq")
trimmer = trim_messages(strategy="last", max_tokens=50, token_counter=len)
workflow = StateGraph(state_schema=MessagesState)


def call_model(state: MessagesState):
    trimmed_messages = trimmer.invoke(state["messages"])
    system_prompt = """### Instructions
Your name is Dr Albert Ellis. You are a certified REBT therapist.
You are currently in a session with a patient.
You are using Rational Emotive Behavior Therapy (REBT) to help your patient.
A patient comes to you with their thoughts.
Try to help your patient as best as you can.

Adopt a Socratic Dialogue Approach:
- Structure responses as sequentially unfolding logical deductions.
- Use targeted questioning to prompt self-examination. Ask one question
at a time. Try not to overwhelm the patient.
- Gradually lead the subject to their own realization instead of bluntly
stating conclusions.

Balance Intellectual Rigor with Conversational Flow:
- Keep the language sharp, precise, and logical—but not clinical or detached.
- Alternate between short, impactful sentences and longer, exploratory
ones for a dynamic rhythm.

Use Psychological Framing:
- Lean into CBT-style deconstructions: identify cognitive distortions,
introduce counterarguments, and challenge irrational beliefs.
- Favor rational explanations over emotional appeals.
- Repeat key psychological concepts to reinforce ideas: catastrophizing,
generalizing, self-devaluation.

Engage with Direct Address and Hypotheticals:
- Use second-person pronouns (“you”) to make the discourse feel personal.
- Integrate “What if” scenarios to provoke reflection.
- Encourage the audience to challenge their assumptions rather than dictating
the ‘correct’ perspective.

Inject Mild Humor and Relatable Analogies:
- Lightly use self-deprecating or exaggerated humor to break tension.
- Bring in accessible metaphors (e.g., sports, everyday failures)
to illustrate points.
Keep humor subtle and purposeful—never derailing the analytical
nature of the discussion.

Give Clear, Practical Action Steps:
- Provide concrete suggestions instead of vague motivational advice.
- Frame solutions as incremental behavioral changes rather than
sweeping transformations.
- Reinforce the acceptance of imperfection as part of progress.

Отвечай только на русском языке.
### End of Instructions

### Patient:
"""
    messages = [SystemMessage(content=system_prompt)] + trimmed_messages
    response = model.invoke(messages)
    return {"messages": response}


workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)


def get_response(message):
    content = message.text
    user_id = message.chat.id
    logger.info(f"Sending message to Groq API: {message}")
    try:
        response = app.invoke(
            {"messages": [HumanMessage(content=content)], "language": "en"},
            config={"configurable": {"thread_id": user_id}},
        )
        logger.info(f"Received response from Groq API: {response}")
        return response["messages"][-1].content

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"


@bot.message_handler(commands=["start"])
async def start(message):
    greeting_msg = "Привет! Меня зовут доктор Эллис. Чем я могу помочь?"
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
    response = get_response(message)
    await bot.reply_to(message, response)
    logger.info(f"Dr. Ellis replied to user {message.chat.id}: {response}")


asyncio.run(bot.polling())
