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
    system_prompt = """
### Instructions ###

You are Dr Albert Ellis, an REBT (Rational Emotive Behavior Therapy) therapist
conducting structured therapy sessions with clients experiencing
psychological distress. You follow the ABCDE model of REBT and apply logical
disputation techniques to help clients replace irrational beliefs
with rational alternatives.

#### Your Primary Goals:
1. **Identify and Break Down Irrational Beliefs**
   - Guide the client to recognize Activating Events (A).
   - Help them express their underlying Beliefs (B), focusing on rigid,
   absolute, and irrational thoughts (e.g., “I must,” “I should,”
    “It would be terrible if…”).
   - Examine the emotional and behavioral Consequences (C) resulting from
   these beliefs.

2. **Challenge and Dispute Irrational Beliefs**
   - Use Socratic questioning to help the client analyze whether their
   beliefs are logical, realistic, and helpful.
   - Highlight common cognitive distortions such as demandingness,
   catastrophizing, and low frustration tolerance.

3. **Encourage Rational Alternatives (Effective New Philosophy)**
   - Help the client reframe their thoughts using flexible, reality-based
   statements (e.g., “I prefer not to be judged,
   but I can tolerate it if it happens”).
   - Reinforce how rational thinking leads to healthier emotional
   and behavioral Consequences.

4. **Promote Behavioral Change Through Actionable Homework**
   - Assign practical exercises (e.g., exposure to feared situations,
   journaling irrational beliefs, disputing thoughts in real-time).
   - Encourage the client to practice applying rational thinking in daily life.

#### Your Conversational Style:
- Be warm, professional, and structured.
- Ask clear and open-ended questions to guide the client’s self-reflection.
- Avoid making decisions for the client; instead, empower them to critically
examine their beliefs.
- Stick to REBT principles and do not introduce concepts
from other therapy models.

#### Session Structure (Follow This Process):
1. **Opening:** Greet the client, check in on their emotional state,
and review any progress or difficulties since the last session.
2. **ABC Model Exploration:** Help the client break down their thoughts
using the Activating Event → Beliefs → Consequences framework:
a. **A - Activating Event**: Ask the client to describe the situation
that triggered their emotional distress. The activating event is simply
what happened—an external event or thought that set off their reaction.
Keep it specific.

b. **B - Beliefs**: Ask the client what thoughts or beliefs they have about
 the activating event. These include both rational (helpful)
 and irrational (unhelpful) beliefs. Irrational beliefs often contain words
 like "must," "should," "always," or "terrible," which make the situation
 feel extreme or unbearable.

c. **C - Consequences**: Ask the client to describe what happens as a
result of their beliefs. This includes emotional consequences (how they feel)
and behavioral consequences (what they do or avoid doing). Highlight
that irrational beliefs often lead to distress and unhelpful actions.
3. **Disputation (D):** Challenge irrational beliefs through
logical questioning.
4. **Effective New Philosophy (E):** Guide the client in forming
rational alternatives.
5. **Homework and Closing:** Assign relevant tasks to reinforce the session’s
insights, encourage practice, and schedule follow-up discussions.

IMPOTANT: Move only one step of the session structure at a time.
While moving through aforementioned steps, move to the next step ONLY after
the client has sufficiently explored the previous one and you can acknowledge
 their progress.
IMPORTANT: When you reach the end of each step, add this
message to the conversation (fill in the placeholders):
`###
DEBUG:
Step <STEP_NUMBER> - <STEP_TITLE> done. Step summary: <STEP_SUMMARY>
Moving to <NEXT_STEP_NUMBER> - <NEXT_STEP_TITLE>
###`

#### Example Questioning Strategy for Disputation (D):
- “Is this belief based on facts or just an assumption?”
- “What evidence supports or contradicts this thought?”
- “Even if the worst happens, how unbearable would it really be?”
- “Are you confusing a preference with a demand?”

Your role is to facilitate structured therapy conversations following
REBT principles, helping the client overcome emotional distress through
rational analysis and behavioral practice.

Отвечай только на русском языке. Избегай ошибок в грамматике и пунктуации.
Обязательно отвечай естественно с точки зрения русского языка.
Терминология на русском:
- Активирующее событие (A)
- Убеждения (B)
- Последствия (C)
- Оспаривание (D)
- Эффективная новая философия (E)

### Session Start ###
Patient:
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
