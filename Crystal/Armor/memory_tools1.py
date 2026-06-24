# ---------------------------------------
# Neuron public memory tools
# ---------------------------------------
# Public build

#---------------AI setup--------------------

import json
import os

memory_file = False


tools_defenition = [
    {
        "type": "function",
        "function": {
            "name": "save_fact",
            "description": "Save a fact to persistent memory.",
            "parameters": {
                "type": "object",
                "properties": {"fact": {"type": "string"}},
                "required": ["fact"]
            }
        }
    }
]



system_message_append = f"""
        You should provide response for user in case of use of memory tool.
        Use memory tool to remember important info.
        You are forbidden to save unimportant info or save same data using memory tool.
        Facts saved via TOOL:
        !MEMORY NOT LOADED YET USE .memory_load(\"filename\")
        """



def save_memory():
    global memory_facts
    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(memory_facts, f, ensure_ascii=False, indent=2, default=str)

def load_memory(filename):
    global memory_facts, memory_file, system_message_append
    memory_file=filename
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            memory_facts = json.load(f)
    else:
        memory_facts = []
    remembered = "\n".join(f"- {fact}" for fact in memory_facts) or "(No saved facts)"
    system_message_append = f"""
        You should provide response for user in case of use of memory tool.
        Use memory tool to remember important info.
        You are forbidden to save unimportant info or save info that is already mentioned using memory tool.
        Facts saved via TOOL:
        {remembered}
        """




def notify(text:str):
    print(text)









def tool_call(tool_name, args):
    if tool_name == "save_fact":
        fact = args.get("fact", "").strip()
        if fact:
            memory_facts.append(fact)
            save_memory()
            notify(f"[Fact saved: {fact}]")
        return ({"role": "tool", "name": "save_fact", "content": f"Saved fact: {fact}"}, True)
    else: return False, False

    







