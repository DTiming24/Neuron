# ---------------------------------------
# Neuron public web tools
# ---------------------------------------
# Public build

DEBUG = False

try:
    from ddgs import DDGS
except Exception:
    DDGS = None

import time

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

#from playwright_stealth import Stealth
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

import warnings

warnings.filterwarnings("ignore")




# ----------------------------
# Page fetcher (replacement)
# ----------------------------
def web_page(url, max_paragraphs=20, scroll=True):
    if sync_playwright is None or BeautifulSoup is None:
        return "[Web page tool unavailable: install playwright and beautifulsoup4.]"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.243 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded")
        time.sleep(2)

        if scroll:
            last_height = 0
            while True:
                new_height = page.evaluate(
                    """() => { const s = document.body.scrollHeight; window.scrollTo(0,s); return s; }"""
                )
                if new_height == last_height:
                    break
                last_height = new_height
                time.sleep(0.5)

        html = page.content()
        browser.close()

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form", "iframe", "button"]):
            tag.decompose()

        paragraphs = [tag.get_text(strip=True) for tag in soup.find_all(["p", "h1", "h2", "h3"]) if tag.get_text(strip=True)]
        if not paragraphs:
            return "[No text found on page]"
        return "\n\n".join(paragraphs[:max_paragraphs])
# ----------------------------
# Web search tool
# ----------------------------
last_web_query = None

def notify(text):
    print(text)

def web_search(query, max_results=10):
    if DDGS is None:
        return "[Web search unavailable: install ddgs.]"
    try:
        with DDGS() as searcher:
            results = list(searcher.text(query, max_results=max_results))
        if not results:
            notify("[Web search - no results found.]")
            return "No results found."

        formatted = []
        for r in results:
            formatted.append(
                f"{r.get('title','No title')}\n{r.get('body','')}\n{r.get('href','')}\n"
            )
        return "\n".join(formatted)
    except Exception as e:
        return f"[Web search error] {e}"

def smart_web_search(query):
    global last_web_query
    if last_web_query == query:
        notify(f"[Web search denied for: {query}]")
        return "(Already searched recently)"
    last_web_query = query
    return web_search(query)


# ----------------------------
# Tool call
# ----------------------------

tools_defenition = [
    {
        "type": "function",
        "function": {
            "name": "web_search_tool",
            "description": "Perform a web search and return formatted results",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_page_tool",
            "description": "Fetch text content from a webpage URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "max_paragraphs": {"type": "integer"}
                },
                "required": ["url"]
            }
        }
    }
]


system_message_append = """
Don't use the same page.
Don't use web search tool orweb page tool again, unless nessesary.
Use web search for info that ma yhave changed.
"""

def tool_call(tool_name, args):
    if tool_name == "web_search_tool":
        notify("Web search triggered.")
        return {
            "role": "tool",
            "name": "web_search_tool",
            "content": smart_web_search(args.get("query", ""))
        }, True

    elif tool_name == "web_page_tool":
        notify("Web page triggered.")
        return {
            "role": "tool",
            "name": "web_page_tool",
            "content": web_page(
                args.get("url", ""),
                max_paragraphs=args.get("max_paragraphs", 20)
            )
        }, True

    return False, False
