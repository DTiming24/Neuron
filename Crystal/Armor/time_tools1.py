# ---------------------------------------
# Neuron public time tools
# ---------------------------------------
# Public build






from datetime import datetime





#!No built in tools
#tools_defenition = [
#
#]






def date_time():
    return str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


def system_message_append():
    return f"""
    Current local date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """








def notify(text:str):
    print(text)



#!No built in tools
#def tool_call(tool_name, args):
#    if tool_name == "run_cmd":
#        cmd = args.get("command", "")
#        notify(f"[DEBUG] Cmd command: {cmd}.")
#        try:
#            output = subprocess.getoutput(cmd, encoding="cp437")
#            notify(f"[DEBUG] Cmd output:\n{output}\n[DEBUG] Cmd output end.")
#        except Exception as e:
#            output = f"(CMD execution error: {e})"
#        return({"role": "tool", "name": "web_page_tool", "content": "Run cmd tool: "+ str(output)},True)

    





