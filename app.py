from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import json
import os
from dotenv import load_dotenv

# === 載入 .env ===
load_dotenv()

PASSWORD = os.getenv("APP_PASSWORD")
SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

app = Flask(__name__)
app.secret_key = SECRET_KEY

DATA_FILE = "data.json"

# === 初始化資料檔 ===
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_target(data, path_list):
    """根據 path_list 找到目標層"""
    current = data
    for p in path_list:
        if p not in current:
            current[p] = {}
        current = current[p]
    return current


# === 登入頁面 ===
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        input_pwd = request.form.get("password", "").strip()
        if input_pwd == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            return render_template_string("""
                <h2>密碼錯誤</h2>
                <a href="/login">返回登入</a>
            """)

    return render_template_string("""
        <h2>請輸入密碼以進入系統</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="輸入密碼">
            <button type="submit">登入</button>
        </form>
    """)


# === 登出 ===
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# === 主頁（需登入） ===
@app.route("/", methods=["GET"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return render_template_string("""
        <h2>JSON 多層管理工具</h2>
        <a href="/logout">登出</a><br><br>

        <h3>插入 / 修改</h3>
        <form method="POST" action="/insert">
            <label>插入路徑（例如 chatgpt/sub1，留空=最外層）:</label><br>
            <input type="text" name="path" placeholder="chatgpt/sub1"><br><br>

            <label>Key:</label><br>
            <input type="text" name="key"><br><br>

            <label>Value (可用逗號分隔多值):</label><br>
            <input type="text" name="value"><br><br>

            <button type="submit">插入 / 修改</button>
        </form>

        <h3>刪除</h3>
        <form method="POST" action="/delete">
            <label>目標路徑（例如 chatgpt/sub1，留空=最外層）:</label><br>
            <input type="text" name="path" placeholder="chatgpt/sub1"><br><br>

            <label>要刪除的 Key:</label><br>
            <input type="text" name="key"><br><br>

            <button type="submit">刪除</button>
        </form>

        <h3>目前 JSON</h3>
        <pre id="json-display">{{ json_data }}</pre>
    """, json_data=json.dumps(load_data(), ensure_ascii=False, indent=4))


@app.route("/insert", methods=["POST"])
def insert():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    path = request.form.get("path", "").strip()
    key = request.form.get("key", "").strip()
    value_raw = request.form.get("value", "").strip()

    if not key:
        return "Key 不能為空", 400

    values = [v.strip() for v in value_raw.split(",")] if "," in value_raw else value_raw

    data = load_data()
    path_list = [p for p in path.split("/") if p]
    target = get_target(data, path_list)
    target[key] = values
    save_data(data)

    return render_template_string("""
        <h2>已更新資料！</h2>
        <a href="/">返回</a>
        <pre>{{ json_data }}</pre>
    """, json_data=json.dumps(data, ensure_ascii=False, indent=4))


@app.route("/delete", methods=["POST"])
def delete():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    path = request.form.get("path", "").strip()
    key = request.form.get("key", "").strip()

    if not key:
        return "Key 不能為空", 400

    data = load_data()
    path_list = [p for p in path.split("/") if p]
    target = get_target(data, path_list)

    if key in target:
        del target[key]
        save_data(data)
        message = f"已刪除 {path}/{key}"
    else:
        message = f"找不到 {path}/{key}"

    return render_template_string("""
        <h2>{{ message }}</h2>
        <a href="/">返回</a>
        <pre>{{ json_data }}</pre>
    """, message=message, json_data=json.dumps(data, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    app.run()
