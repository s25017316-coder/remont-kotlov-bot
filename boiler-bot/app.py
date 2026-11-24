import os
import json
import threading
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "9035492152:AAFExmRGivwbNcAgwTkTvEL1Sav18ttuRXQ")
RECIPIENTS = [7668006338, 9191128026]
STATE_FILE = "bot_state.json"

state_lock = threading.Lock()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "offset": data.get("offset", 0),
                "sources": data.get("sources", {}),
                "total_leads": data.get("total_leads", 0),
            }
    return {"offset": 0, "sources": {}, "total_leads": 0}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def tg_request(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception:
        return None


def send_to_chat(chat_id, text):
    tg_request("sendMessage", {
        "chat_id": chat_id,
        "text": text,
    })


def format_stats(state):
    sources = state.get("sources", {})
    total = state.get("total_leads", 0)

    if not sources or total == 0:
        return "Аналитика пока пустая: заявок ещё не было."

    sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
    lines = [f"Аналитика источников (всего заявок: {total}):\n"]
    for idx, (source_name, count) in enumerate(sorted_sources, start=1):
        percent = round((count / total) * 100)
        lines.append(f"{idx}. {source_name} — {count} ({percent}%)")

    top_source = sorted_sources[0][0]
    lines.append(f"\nЧаще всего приходят из: {top_source}")
    return "\n".join(lines)


def handle_update(update, state):
    if "message" not in update:
        return

    msg = update["message"]
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = (msg.get("text") or "").strip()

    if text.startswith("/start"):
        send_to_chat(
            chat_id,
            "Бот активен. Заявки с сайта remont-kotlov-almaty.kz будут приходить сюда.\n"
            "Команда аналитики: /stats"
        )
    elif text.startswith("/stats"):
        send_to_chat(chat_id, format_stats(state))


def poll_telegram():
    while True:
        try:
            with state_lock:
                state = load_state()
                offset = state["offset"]

            data = tg_request("getUpdates", {
                "offset": offset,
                "timeout": 20,
                "allowed_updates": ["message"],
            })

            if data and data.get("ok"):
                results = data.get("result", [])
                if results:
                    with state_lock:
                        state = load_state()
                        for upd in results:
                            handle_update(upd, state)
                            state["offset"] = upd["update_id"] + 1
                        save_state(state)
        except Exception:
            pass
        time.sleep(2)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET"
    return response


@app.route("/", methods=["GET"])
def health():
    return "OK", 200


@app.route("/api/lead", methods=["POST", "OPTIONS"])
def create_lead():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    model = (payload.get("model") or "не указана").strip()
    location = (payload.get("location") or "Алматы и Алатау").strip()
    source = (payload.get("source") or "Не указан").strip()
    master_phone = (payload.get("masterPhone") or "+7 771 544 27 86").strip()

    if not name or not phone:
        return jsonify({"ok": False, "error": "Укажите имя и телефон"}), 400

    with state_lock:
        state = load_state()
        state["total_leads"] = state.get("total_leads", 0) + 1
        state["sources"][source] = state["sources"].get(source, 0) + 1
        save_state(state)

    text = (
        f"НОВАЯ ЗАЯВКА НА РЕМОНТ КОТЛА ({master_phone})\n\n"
        f"Клиент: {name}\n"
        f"Телефон: {phone}\n"
        f"Локация: {location}\n"
        f"Котёл: {model}\n"
        f"Источник: {source}"
    )

    for chat_id in RECIPIENTS:
        send_to_chat(chat_id, text)

    return jsonify({"ok": True}), 200


threading.Thread(target=poll_telegram, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)