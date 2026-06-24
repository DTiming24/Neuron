import os

from openai import OpenAI

API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

system_message_append = """
You are a helpful assistant.
Keep responses clear, concise, and natural.
"""


def notify(text: str):
    print(text)


def chat(sys_message, tools, model="", short_memory=None):
    if short_memory is None:
        short_memory = []
    messages = [sys_message, *short_memory]
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            tools=tools,
        )
        choice = completion.choices[0]
        reply = choice.message.content or ""
        if reply and "analysisUser" in reply:
            reply = reply.removeprefix("assistantfinal")
        if choice.message.tool_calls:
            return reply, choice.message.tool_calls
        return reply, False
    except Exception as e:
        reply = f"(Error: {e})"
        print(reply)
        return reply, False
