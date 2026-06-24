import json
import os
from pathlib import Path

import bleach
import markdown
from flask import Flask, abort, jsonify, redirect, render_template_string, request, session, url_for

import chat_prossesor_1 as cp

BASE_DIR = Path(__file__).resolve().parents[2]
USERS_FILE = Path(os.environ.get("NEURON_USERS_FILE", str(BASE_DIR / "users.json")))

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-for-production")

USER_PERMS = ["user", "admin", "root", "system"]

MD_EXTENSIONS = [
    "fenced_code", "tables", "nl2br", "sane_lists",
    "codehilite", "extra",
    "pymdownx.extra", "pymdownx.tilde"
]

ALLOWED_TAGS = [
    "p", "br", "hr", "strong", "em", "ul", "ol", "li",
    "blockquote", "pre", "code", "table", "thead", "tbody",
    "tr", "th", "td", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "span", "div", "del"
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "code": ["class"],
    "span": ["class"],
    "div": ["class"],
}


def render_markdown(text: str) -> str:
    html = markdown.markdown(text, extensions=MD_EXTENSIONS)
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )


def ch(session_obj, level=""):
    username = session_obj.get("username")
    if not username:
        return False
    users = load_users()
    user = users.get(username)
    if user and user.get("active"):
        if level == "":
            return True
        if user.get("role") in USER_PERMS[USER_PERMS.index(level):]:
            return True
    return False


def ch_p(session_obj):
    username = session_obj.get("username")
    if not username:
        return False
    users = load_users()
    user = users.get(username)
    return bool(user and user.get("active") and user.get("private"))


def ch_r(session_obj):
    username = session_obj.get("username")
    if not username:
        return False
    users = load_users()
    user = users.get(username)
    return bool(user and user.get("active") and user.get("role") == "root")


def load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        with USERS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_users(users):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


def read_html(name: str) -> str:
    return (BASE_DIR / "html" / name).read_text(encoding="utf-8")


HTML_LOGIN = read_html("login.html")
HTML_CHAT = read_html("chat.html")
HTML_WELCOME_BACK = read_html("welcome_back.html")
HTML_DASHBOARD = read_html("dashboard.html")
HTML_SETTINGS = read_html("settings.html")
HTML_CHANGE_PASSWORD = read_html("change_password.html")
HTML_USER_MANAGEMENT = read_html("user_management.html")


@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
def login():
    if ch(session):
        return redirect(url_for("dashboard_page"))
    if request.method == "GET":
        return render_template_string(HTML_LOGIN)

    username = request.form.get("username")
    password = request.form.get("password")

    users = load_users()
    user = users.get(username)

    if user and password == user.get("password") and user.get("active"):
        session["username"] = username
        return redirect(url_for("welcome_back_page"))

    message = '<span style="color: red;">Invalid username, password or account is inactive</span>'
    return render_template_string(HTML_LOGIN, message=message)


@app.route("/logout")
def logout_page():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/welcome_back", methods=["GET"])
def welcome_back_page():
    if not ch(session):
        return redirect(url_for("login"))
    return render_template_string(HTML_WELCOME_BACK, username=session.get("username"))


@app.route("/admin_tools", methods=["GET"])
def admin_tools_page():
    if not ch(session, "admin"):
        abort(403)
    return redirect(url_for("user_management"))


@app.route("/neuron/chat", methods=["GET"])
def neuron_chat_page():
    if not ch(session):
        return redirect(url_for("login"))
    return render_template_string(HTML_CHAT)


@app.route("/dashboard", methods=["GET"])
def dashboard_page():
    if not ch(session):
        return redirect(url_for("login"))
    return render_template_string(
        HTML_DASHBOARD,
        username=session.get("username"),
        is_admin=ch(session, "admin"),
    )


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if not ch(session):
        return redirect(url_for("login"))
    return redirect(url_for("settings_change_password_page"))


@app.route("/settings/change_password", methods=["GET", "POST"])
def settings_change_password_page():
    if not ch(session):
        return redirect(url_for("login"))

    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        username = session.get("username")
        users = load_users()
        user = users.get(username)
        if not user:
            return redirect(url_for("login"))
        if new_password and new_password == confirm_password and old_password == user.get("password"):
            users[username]["password"] = new_password
            save_users(users)
            return redirect(url_for("dashboard_page"))
        if old_password != user.get("password"):
            error = "Old password is incorrect."
            return render_template_string(HTML_CHANGE_PASSWORD, error=error)
        error = "Passwords do not match or are empty."
        return render_template_string(HTML_CHANGE_PASSWORD, error=error)

    return render_template_string(HTML_CHANGE_PASSWORD)


@app.route("/neuron/api/request", methods=["POST"])
def neuron_chat_api():
    if not ch(session):
        return abort(403)

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"]
    if user_message.startswith("!web"):
        if not ch(session, "admin"):
            return jsonify({"response": "(Error: Admin privileges required.)"})
        command = user_message[4:].strip()
        if command == "rst":
            import sys
            os.execv(sys.executable, [sys.executable] + sys.argv)
            sys.exit(0)
        if command == "uht":
            global HTML_LOGIN, HTML_CHAT, HTML_WELCOME_BACK, HTML_DASHBOARD, HTML_SETTINGS, HTML_CHANGE_PASSWORD, HTML_USER_MANAGEMENT
            HTML_LOGIN = read_html("login.html")
            HTML_CHAT = read_html("chat.html")
            HTML_WELCOME_BACK = read_html("welcome_back.html")
            HTML_DASHBOARD = read_html("dashboard.html")
            HTML_SETTINGS = read_html("settings.html")
            HTML_CHANGE_PASSWORD = read_html("change_password.html")
            HTML_USER_MANAGEMENT = read_html("user_management.html")
            return jsonify({"response": "HTML files reloaded."})

    response = cp.pross(message=user_message, username=session.get("username"), private=ch_p(session))
    return jsonify({"response": render_markdown(response)})


@app.route("/admin_tools/user_management")
def user_management():
    if not ch(session, "admin"):
        return abort(403)

    users = load_users()
    visible_users = {}

    for username, user in users.items():
        role = user.get("role", "user")
        role_index = USER_PERMS.index(role) if role in USER_PERMS else 0
        next_level = USER_PERMS[min(role_index + 1, len(USER_PERMS) - 1)]
        if not ch(session, next_level):
            continue
        visible_users[username] = user

    return render_template_string(HTML_USER_MANAGEMENT, users=visible_users)


@app.route("/admin_tools/user_management/update", methods=["POST"])
def user_management_update():
    if not ch(session, "admin"):
        return abort(403)

    users = load_users()
    to_delete = []

    for username, user in users.items():
        active = request.form.get(f"active_{username}") == "true"
        private = request.form.get(f"private_{username}") == "true"
        password = request.form.get(f"password_{username}")
        role = request.form.get(f"role_{username}")

        if not active:
            to_delete.append(username)
            continue
        user["active"] = active
        user["private"] = private
        if password:
            user["password"] = password
        if role and role in USER_PERMS:
            user["role"] = role

    for username in to_delete:
        users.pop(username, None)

    save_users(users)
    return redirect(url_for("user_management"))


@app.route("/admin_tools/user_management/new_user", methods=["POST"])
def user_management_new_user():
    if not ch(session, "admin"):
        return abort(403)

    users = load_users()
    new_username = request.form.get("new_username")
    new_password = request.form.get("new_password")
    new_active = request.form.get("new_active") == "true"
    if new_username in users:
        return render_template_string(HTML_USER_MANAGEMENT, users=users, error="User already exists")
    users[new_username] = {"active": new_active, "role": "user", "password": new_password, "private": False}
    save_users(users)
    return redirect(url_for("user_management"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
