# ---------------------------------------
# Neuron public system tools
# ---------------------------------------
# Public build






from datetime import datetime
import subprocess





tools_defenition = [
    {
        "type": "function",
        "function": {
            "name": "run_cmd",
            "description": "Run a Windows CMD command and return the output.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_prg",
            "description": "Run a programm.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    }
]








system_message_append = f"""
If user asks to work with system use tool run_cmd, newer ask user to do something use cmd tool to do it yourself (you may call powershell or an other programm from it).
If user asks to open programm you should use run_prg tool.
Current local date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""








def notify(text:str):
    print(text)




def tool_call(tool_name, args):
    if tool_name == "run_cmd":
        cmd = args.get("command", "")
        notify(f"[DEBUG] Cmd command: {cmd}.")
        try:
            output = subprocess.getoutput(cmd, encoding="cp437")
            notify(f"[DEBUG] Cmd output:\n{output}\n[DEBUG] Cmd output end.")
        except Exception as e:
            output = f"(CMD execution error: {e})"
        return({"role": "tool", "name": "run_cmd", "content": "Run cmd tool: "+ str(output)},True)

    
    elif tool_name == "run_prg":
        path = args.get("path", "")
        notify(f"[DEBUG] Programm started: {path}.")
        try:
            output = subprocess.getoutput("start \"\" \""+path+"\"", encoding="cp437")
            notify(f"[DEBUG] Cmd output:\n{output}\n[DEBUG] Cmd output end.")
        except Exception as e:
            output = f"(Programm execution error: {e})"
        return({"role": "tool", "name": "run_prg", "content": "Run prg tool: "+ str(output)},False)
    else: return False, False





