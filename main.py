import asyncio
import sqlite3
import random
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ =====
TOKEN = "8483342131:AAEI7X0IxLgLHK4n6UhSTVG_RizXKqnOYmY"
YOUR_USER_ID = 7968128384

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect('femboy_love.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        gender TEXT,
        trust INTEGER DEFAULT 0,
        last_morning TEXT,
        last_night TEXT
    )
''')
conn.commit()

def get_user(user_id):
    cursor.execute('SELECT name, gender, trust FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return {"name": row[0], "gender": row[1], "trust": row[2]}
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
    cursor.execute('SELECT trust FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone()[0]

def can_send_morning(user_id):
    today = datetime.now().date().isoformat()
    cursor.execute('SELECT last_morning FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    return not (row and row[0] == today)

def mark_morning_sent(user_id):
    today = datetime.now().date().isoformat()
    cursor.execute('UPDATE users SET last_morning = ? WHERE user_id = ?', (today, user_id))
    conn.commit()

def can_send_night(user_id):
    today = datetime.now().date().isoformat()
    cursor.execute('SELECT last_night FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    return not (row and row[0] == today)

def mark_night_sent(user_id):
    today = datetime.now().date().isoformat()
    cursor.execute('UPDATE users SET last_night = ? WHERE user_id = ?', (today, user_id))
    conn.commit()

def get_all_users():
    cursor.execute('SELECT user_id FROM users')
    return [row[0] for row in cursor.fetchall()]

# ===== ФРАЗЫ =====
def get_flirt(trust, name, gender):
    if gender == "девушка":
        if trust < 20:
            return f"*смущённо* Ты такая красивая, {name}... *опускает глаза*"
        elif trust < 50:
            return f"*берёт за руку* С тобой так спокойно, {name}... *шепчет* Ты особенная."
        elif trust < 80:
            return f"*прижимается щекой* Твои волосы так вкусно пахнут... *целует в плечо*"
        else:
            return f"*смотрит с желанием* Я хочу быть только твоим... *тянется к губам*"
    else:
        if trust < 20:
            return f"*игриво* Привет, {name}... Ты сегодня такой классный *улыбается*"
        elif trust < 50:
            return f"*кладёт голову на плечо* С тобой мне тепло... *шепчет*"
        elif trust < 80:
            return f"*страстно целует* Ммм... Не останавливайся..."
        else:
            return f"*стонет тихо* Я хочу тебя... Прямо сейчас... *обнимает*"

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
    user_id = update.effective_user.id
    update_gender(user_id, "девушка")
    await update.message.reply_text("*радостно* Ах вот как... Значит, ты моя хозяйка ❤️ *улыбается*", parse_mode="Markdown")

async def set_boy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_gender(user_id, "парень")
    await update.message.reply_text("*кивает* Понял... Ты мой хозяин. Я буду слушаться ❤️", parse_mode="Markdown")

async def flirt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Сначала напиши /girl или /boy, чтобы я знал, кто ты ❤️")
        return
    trust = data["trust"]
    gender = data["gender"]
    phrase = get_flirt(trust, name, gender)
    await update.message.reply_text(phrase, parse_mode="Markdown")
    add_trust(user_id, 1)

async def kiss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Сначала напиши /girl или /boy ❤️")
        return
    trust = data["trust"]
    if trust < 30:
        await update.message.reply_text("*краснеет* Ещё рано... Давай сначала познакомимся ближе? *стесняется*", parse_mode="Markdown")
    else:
        await update.message.reply_text("*страстно целует, обвивая руками шею* Ммм... Ты мой сладкий...", parse_mode="Markdown")
        add_trust(user_id, 2)

async def hug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Сначала напиши /girl или /boy ❤️")
        return
    await update.message.reply_text("*крепко обнимает, утыкаясь носом в плечо* Я так рад тебя видеть...", parse_mode="Markdown")
    add_trust(user_id, 1)

async def trust_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user(user_id)
    if not data:
        await update.message.reply_text("Напиши /start, чтобы познакомиться ❤️")
        return
    await update.message.reply_text(f"❤️ Уровень доверия: {data['trust']}/100. Чем больше — тем ближе я буду к тебе.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    text = update.message.text.lower()
    data = get_user(user_id)
    if not data or not data["gender"]:
        await update.message.reply_text("Напиши /girl или /boy, чтобы я понял, кто ты ❤️")
        return
    trust = data["trust"]
    gender = data["gender"]
    if "привет" in text:
        await update.message.reply_text(get_flirt(trust, name, gender), parse_mode="Markdown")
    elif "как дела" in text:
        await update.message.reply_text("*вздыхает* Скучал по тебе... А у тебя как? *с надеждой*", parse_mode="Markdown")
    elif "обними" in text:
        await hug(update, context)
    elif "поцелуй" in text:
        await kiss(update, context)
    else:
        await update.message.reply_text("*слушает внимательно* Мне интересно всё, что ты говоришь... Расскажи ещё ❤️", parse_mode="Markdown")

# ===== ФОНОВАЯ ЗАДАЧА (через asyncio.create_task) =====
async def auto_sender(app):
    while True:
        now = datetime.now()
        if now.hour == 7 and now.minute == 0:
            for uid in get_all_users():
                if can_send_morning(uid):
                    try:
                        await app.bot.send_message(uid, "*Доброе утро, сладкий... Я уже проснулся и думаю о тебе ❤️*", parse_mode="Markdown")
                        mark_morning_sent(uid)
                    except:
                        pass
            await asyncio.sleep(60)
        elif now.hour == 22 and now.minute == 0:
            for uid in get_all_users():
                if can_send_night(uid):
                    try:
                        await app.bot.send_message(uid, "*Спокойной ночи, любимый... Приснись мне. Целую 🤗*", parse_mode="Markdown")
                        mark_night_sent(uid)
                    except:
                        pass
            await asyncio.sleep(60)
        await asyncio.sleep(30)

# ===== ЗАПУСК (ПРОСТОЙ И РАБОЧИЙ) =====
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

    # Запускаем авторассылку в фоне
    loop = asyncio.get_event_loop()
    loop.create_task(auto_sender(app))

    print("✅ Фембойчик запущен. Пол, доверие, авторассылка — всё работает.")
    app.run_polling()

if __name__ == "__main__":
    main()
