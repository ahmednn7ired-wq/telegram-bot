import os
# ===== ПРОВЕРКА ЗАПУСКА ФАЙЛА =====
print("ФАЙЛ bot.py ЗАПУЩЕН")

import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ===== НАСТРОЙКИ =====

TOKEN = TOKEN = os.getenv("8315164729:AAGIs5fCGR2fFUjtCpQYLYpjpf14zrAA5uw")
        
ADMIN_ID = 5623880358   # ← ВСТАВЬ СЮДА СВОЙ TELEGRAM ID (ЦИФРЫ!)

CHANNELS = [
    "@progfam"
]

# ===== БАЗА ДАННЫХ =====

db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS videos (
    file_id TEXT PRIMARY KEY
)
""")

db.commit()

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def is_subscribed(user_id, context):
    for channel in CHANNELS:
        member = await context.bot.get_chat_member(channel, user_id)
        if member.status not in ("member", "administrator", "creator"):
            return False
    return True


def user_received_video(user_id):
    cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


def save_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    db.commit()


def get_random_video():
    cursor.execute("SELECT file_id FROM videos ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else None


def subscribe_keyboard():
    buttons = []
    for ch in CHANNELS:
        buttons.append([
            InlineKeyboardButton(
                f"📢 Подписаться {ch}",
                url=f"https://t.me/{ch[1:]}"
            )
        ])
    buttons.append([
        InlineKeyboardButton("✅ Проверить подписку", callback_data="check")
    ])
    return InlineKeyboardMarkup(buttons)

# ===== ХЭНДЛЕРЫ =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("ПОЛУЧЕНА КОМАНДА /start")

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not await is_subscribed(user_id, context):
        await update.message.reply_text(
            "Подпишись на канал, чтобы получить видео 👇",
            reply_markup=subscribe_keyboard()
        )
        return

    if user_received_video(user_id):
        await update.message.reply_text("❌ Ты уже получал видео")
        return

    video = get_random_video()
    if not video:
        await update.message.reply_text("❌ Видео пока не добавлены")
        return

    await context.bot.send_video(chat_id=chat_id, video=video)
    save_user(user_id)


async def check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if not await is_subscribed(user_id, context):
        await query.message.reply_text(
            "❌ Ты не подписан на канал",
            reply_markup=subscribe_keyboard()
        )
        return

    if user_received_video(user_id):
        await query.message.reply_text("❌ Ты уже получал видео")
        return

    video = get_random_video()
    if not video:
        await query.message.reply_text("❌ Видео пока не добавлены")
        return

    await context.bot.send_video(chat_id=chat_id, video=video)
    save_user(user_id)


async def add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("ПОЛУЧЕНО ВИДЕО")

    if update.effective_user.id != ADMIN_ID:
        print("НЕ АДМИН")
        return

    if update.message.video:
        file_id = update.message.video.file_id
        cursor.execute("INSERT OR IGNORE INTO videos VALUES (?)", (file_id,))
        db.commit()
        await update.message.reply_text("✅ Видео добавлено")

# ===== ЗАПУСК =====

def main():
    print("MAIN ЗАПУЩЕН")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="check"))
    app.add_handler(MessageHandler(filters.VIDEO, add_video))

    print("🤖 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ")
    app.run_polling()


if __name__ == "__main__":
    main()
