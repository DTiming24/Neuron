import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import chat_base1 as chat
import memory_tools1 as mem
import time_tools1 as ttime
import web_tools1 as web

BASE_DIR = Path(__file__).resolve().parents[2]
startt = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
short_memory = {}
tools = []


def notify(text: str):
    print(text)


tools.extend(web.tools_defenition)
tools.extend(mem.tools_defenition)


def system_message(username=""):
    if not username:
        raise Exception("Username is required")
    mem.load_memory(str(BASE_DIR / "users" / username / "long_memory.json"))
    system_content = f"""
    You are Neuron, a helpful assistant.
    Rules:
    Keep answers under 100 words.
    Provide accurate, up-to-date information.
    Answer in the user's language.
    Username: {username}
    """ + web.system_message_append + mem.system_message_append + chat.system_message_append + ttime.system_message_append()
    return {"role": "system", "content": system_content.strip()}


def cycle(prompt="", short_memory=None, username=""):
    if short_memory is None:
        short_memory = []
    if not username:
        raise Exception("Username is required")
    if prompt:
        short_memory.append({"role": "user", "content": prompt + "\n" + ttime.date_time()})
    model_response, tool_calls = chat.chat(
        sys_message=system_message(username),
        tools=tools,
        model="z-ai/glm-4.5-air:free",
        short_memory=short_memory[-10:],
    )
    short_memory.append(
        {
            "role": "assistant",
            "content": (model_response.strip() + "\n" + ttime.date_time()) if model_response else "\n" + ttime.date_time(),
            **({"tool_calls": tool_calls} if tool_calls else {}),
        }
    )
    if tool_calls:
        think_end = False
        for tool_call in tool_calls:
            tool_name = getattr(tool_call.function, "name", None)
            raw_args = getattr(tool_call.function, "arguments", "{}")
            try:
                args = json.loads(raw_args)
            except Exception:
                notify(f"[Warning] Failed to parse tool arguments: {raw_args}")
                continue
            response, think = web.tool_call(tool_name=tool_name, args=args)
            if response:
                short_memory.append(response)
                if think:
                    think_end = True
            response, think = mem.tool_call(tool_name=tool_name, args=args)
            if response:
                short_memory.append(response)
                if think:
                    think_end = True
        if think_end:
            return cycle(short_memory=short_memory, username=username)
    return model_response


def pross(message="", username="", private=False):
    global startt, short_memory
    if not username:
        raise Exception("Username is required")
    user_dir = BASE_DIR / "users" / username
    user_dir.mkdir(parents=True, exist_ok=True)
    if username not in short_memory:
        short_memory[username] = []
    if message.startswith("!chat"):
        command = message[5:].strip()
        if command == "sm":
            return str(short_memory[username])
        if command == "csm":
            short_memory[username] = []
            return "Short memory cleared."

    def isolated_cycle():
        return cycle(message, short_memory[username], username)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(isolated_cycle)
        try:
            response = future.result()
            if not private:
                history_path = user_dir / "chat_history.json"
                history = {}
                if history_path.exists():
                    with history_path.open("r", encoding="utf-8") as f:
                        history = json.load(f)
                with history_path.open("w", encoding="utf-8") as f:
                    history[startt] = short_memory[username]
                    json.dump(history, f, ensure_ascii=False, indent=2, default=str)
            return response or "Error: No response"
        except Exception as e:
            return f"Error: {e}"
