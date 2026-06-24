import json
import os
import re
from pathlib import Path

import chat_base1 as chat
import time_tools1 as ttime

BASE_DIR = Path(__file__).resolve().parents[2]

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "request_private_info",
            "description": "Request help from the private info assistant.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
]

system_message_append = """
If the user asks for private information, use the private info tool.
Never reveal passwords, tokens, exact contact details, coordinates, or schedules.
"""

SENSITIVE_KEYWORDS = [
    "address", "location", "coordinates", "latitude", "longitude",
    "phone", "email", "password", "token", "api key", "secret", "ssh",
    "bank account", "card number", "passport", "schedule", "calendar",
    "cookie", "session", "jwt", "private key",
]


def notify(text: str):
    print(text)


def tool_call(tool_name, args):
    if tool_name == "request_private_info":
        query = args.get("query", "").strip()
        response = cycle(query)
        response_lower = response.lower()
        for word in SENSITIVE_KEYWORDS:
            if re.search(rf"\b{re.escape(word)}\b", response_lower):
                print(f"!MESSAGE FILTERED: {word}!")
                return ({"role": "tool", "name": "request_private_info", "content": "Access denied."}, True)
        return ({"role": "tool", "name": "request_private_info", "content": response}, True)
    return False, False


def load_memory(filename):
    memory_file = filename
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            memory_facts = json.load(f)
    else:
        memory_facts = []
    remembered = "\n".join(f"- {fact}" for fact in memory_facts) or "(No saved facts)"
    return f"""
        You should provide a response for the user when the memory tool is used.
        Use memory only for important information.
        Facts saved via TOOL:
        {remembered}
        """


def cycle(prompt="", short_memory=None):
    if short_memory is None:
        short_memory = []
    import chat_base1 as chat

    mem = load_memory(os.environ.get("NEURON_MEMORY_FILE", str(BASE_DIR / "users" / "default" / "long_memory.json")))

    def system_message():
        system_content = f"""
        You are Neuron, a helpful assistant.
        You may share general, non-sensitive information.
        Keep replies under 50 words and use the user's language.
        """ + mem + chat.system_message_append + ttime.system_message_append()
        return {"role": "system", "content": system_content.strip()}

    if prompt:
        short_memory.append({"role": "user", "content": prompt})
    model_response, tool_calls = chat.chat(sys_message=system_message(), tools=[], model="x-ai/grok-4.1-fast", short_memory=short_memory)
    short_memory.append(
        {
            "role": "assistant",
            "content": model_response if model_response else "",
            **({"tool_calls": tool_calls} if tool_calls else {}),
        }
    )
    if tool_calls:
        think_end = False
        for call in tool_calls:
            tool_name = getattr(call.function, "name", None)
            raw_args = getattr(call.function, "arguments", "{}")
            try:
                args = json.loads(raw_args)
            except Exception:
                notify(f"[Warning] Failed to parse tool arguments: {raw_args}")
                continue
            response, think = tool_call(tool_name=tool_name, args=args)
            if response:
                short_memory.append(response)
                if think:
                    think_end = True
        if think_end:
            return cycle(short_memory=short_memory)
    return model_response


def pross(message="", username=False, private=False):
    return cycle(prompt=message)
