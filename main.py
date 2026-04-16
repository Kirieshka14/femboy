import sqlite3
import asyncio
import aiohttp
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8483342131:AAEI7X0IxLgLHK4n6UhSTVG_RizXKqnOYmY"
OPENROUTER_API_KEY = "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"

conn = sqlite3.connect('femboy_brain.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        gender TEXT,
        trust INTEGER DEFAULT 0,
        chat_history TEXT DEFAULT '[]'
    )
''')
conn.commit()

def get_user(user_id):
    cursor.execute('SELECT name, gender, trust, chat_history FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return {"name": row[0], "gender": row[1], "trust": row[2], "chat_history": json.loads(row[3])}
    return None

def set_user(user_id, name, gender=None):
    if gender is None:
        cursor.execute('INSERT OR IGNORE INTO users (user_id, name, trust) VALUES (?, ?, 0)', (user_id, name))
    else:
        cursor.execute('INSERT OR IGNORE INTO users (user_id, name, gender, trust) VALUES (?, ?, ?, 0)', (user_id, name, gender))
    conn.commit()

def update_gender(user_id, gender):
    cursor.execute('UPDATE users SET gender = ? WHERE user_id = ?', (gender, user_id))
    conn.commit()

def add_trust(user_id, delta):
    cursor.execute('UPDATE users SET trust = trust + ? WHERE user_id = ?', (delta, user_id))
    conn.commit()

def save_chat_history(user_id, history):
    cursor.execute('UPDATE users SET chat_history = ? WHERE user_id = ?', (json.dumps(history), user_id))
    conn.commit()

async def ask_femboy(user_message, user_id, name, gender, trust):
    # ПРОСТОЙ ТЕСТ: если не работает ИИ — вернётся этот текст
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [{"role": "user", "content": f"Ты фембойчик. Ответь коротко и мило: {user_message}"}],
                "max_tokens": 100
            }
            async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    return f"*грустно* Ошибка {resp.status}... Но я всё равно тебя люблю ❤️"
    except Exception as e:
        return f"*шепчет* Что-то сломалось... ({str(e)[:30]})"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    set_user(user.id, user.first_name)
    await update.message.reply_text("— Вы мой новый хозяин..? Напиши /girl или /boy ❤️")

async def set_girl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_gender(update.effective_user.id, "девушка")
    await update.message.reply_text("*радостно* Хозяйка! ❤️")

async def set_boy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_gender(update.effective_user.id, "парень")
    await update.message.reply_text("*кивает* Хозяин! ❤️")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Сначала /girl или /boy ❤️")
        return
    reply = await ask_femboy(text, user_id, data["name"], data["gender"], data["trust"])
    await update.message.reply_text(reply)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("girl", set_girl))
    app.add_handler(CommandHandler("boy", set_boy))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
