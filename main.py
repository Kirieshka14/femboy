import sqlite3
import asyncio
import aiohttp
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ (ТОЛЬКО ЭТИ 2 СТРОЧКИ МЕНЯЕШЬ) =====
TOKEN = "8483342131:AAEI7X0IxLgLHK4n6UhSTVG_RizXKqnOYmY"
OPENROUTER_API_KEY = "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"  # Перевыпущенный ключ

# ===== БАЗА ДАННЫХ =====
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

# ===== ЗАПРОС К OPENROUTER =====
async def ask_femboy(user_message, user_id, name, gender, trust):
    user_data = get_user(user_id)
    history = user_data["chat_history"] if user_data else []
    
    if len(history) > 10:
        history = history[-10:]
    
    system_prompt = f"""Ты — фембойчик. Твой характер: милый, игривый, немного стеснительный, но с ростом доверия становишься смелее.
Ты общаешься с {name}. {gender} обращается к тебе.
Уровень доверия: {trust}/100. Чем выше доверие, тем ты откровеннее и ласковее.
Ты не используешь грубых слов, но можешь флиртовать, говорить комплименты, предлагать обнимашки и поцелуи.
Отвечай коротко (1-2 предложения), естественно, как живой человек в Telegram."""
    
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": user_message}]
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": messages,
            "temperature": 0.9,
            "max_tokens": 150
        }
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    reply = result["choices"][0]["message"]["content"]
                else:
                    reply = "*смущённо* Ой, я немного завис... Давай попробуем ещё раз? ❤️"
        except:
            reply = "*поправляет волосы* Что-то пошло не так... Напиши ещё раз, пожалуйста 💕"
    
    new_history = history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": reply}]
    save_chat_history(user_id, new_history)
    
    return reply

# ===== КОМАНДЫ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name
    set_user(user.id, name)
    await update.message.reply_text(
        "— Вы мой новый хозяин..?\n\n"
        "*Фембойчик опускает глаза, теребит край рубашки.*\n\n"
        "— Простите, я волнуюсь... Я буду хорошим. Честно.\n\n"
        "*Он делает маленький шаг вперёд и робко улыбается.*\n\n"
        f"— Меня зовут... ну... можете называть как захотите. А вы? {name}, да?\n\n"
        "*кивает* Красивое имя... Я запомню ❤️\n\n"
        "Только скажите мне: вы девушка или парень? Напишите /girl или /boy",
        parse_mode="Markdown"
    )

async def set_girl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_gender(update.effective_user.id, "девушка")
    await update.message.reply_text("*радостно* Ах вот как... Значит, ты моя хозяйка ❤️ *улыбается*", parse_mode="Markdown")

async def set_boy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_gender(update.effective_user.id, "парень")
    await update.message.reply_text("*кивает* Понял... Ты мой хозяин. Я буду слушаться ❤️", parse_mode="Markdown")

async def flirt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Сначала напиши /girl или /boy ❤️")
        return
    reply = await ask_femboy("пофлиртуй со мной", user_id, data["name"], data["gender"], data["trust"])
    await update.message.reply_text(reply, parse_mode="Markdown")
    add_trust(user_id, 1)

async def kiss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Сначала напиши /girl или /boy ❤️")
        return
    reply = await ask_femboy("я хочу тебя поцеловать", user_id, data["name"], data["gender"], data["trust"])
    await update.message.reply_text(reply, parse_mode="Markdown")
    add_trust(user_id, 2)

async def hug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Сначала напиши /girl или /boy ❤️")
        return
    reply = await ask_femboy("я хочу тебя обнять", user_id, data["name"], data["gender"], data["trust"])
    await update.message.reply_text(reply, parse_mode="Markdown")
    add_trust(user_id, 1)

async def trust_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_user(update.effective_user.id)
    if not data:
        await update.message.reply_text("Напиши /start ❤️")
        return
    await update.message.reply_text(f"❤️ Уровень доверия: {data['trust']}/100. Чем больше — тем ближе я буду к тебе.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Напиши /girl или /boy, чтобы я понял, кто ты ❤️")
        return
    reply = await ask_femboy(text, user_id, data["name"], data["gender"], data["trust"])
    await update.message.reply_text(reply, parse_mode="Markdown")

# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("girl", set_girl))
    app.add_handler(CommandHandler("boy", set_boy))
    app.add_handler(CommandHandler("flirt", flirt))
    app.add_handler(CommandHandler("kiss", kiss))
    app.add_handler(CommandHandler("hug", hug))
    app.add_handler(CommandHandler("trust", trust_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Умный фембойчик запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
