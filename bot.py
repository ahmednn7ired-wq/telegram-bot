mport sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= НАСТРОЙКИ =================

TOKEN = "8315164729:AAGIs5fCGR2fFUjtCpQYLYpjpf14zrAA5uw"
ADMIN_ID = 5623880358 # твой Telegram ID
CHANNEL_USERNAME = "@progfam"
DB_NAME = "bot.db"

# =============================================


# ---------- БАЗА ДАННЫХ ----------

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS videos (
    file_id TEXT
)
""")

conn.commit()


# ---------- ФУНКЦИИ ----------

def user_exists(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone() is not None


def add_user(user_id: int):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    conn.commit()


def save_video(file_id: str):
    cursor.execute("INSERT INTO videos VALUES (?)", (file_id,))
    conn.commit()


def get_videos():
    cursor.execute("SELECT file_id FROM videos")
    return [row[0] for row in cursor.fetchall()]


async def is_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False


# ---------- ХЕНДЛЕРЫ ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(user_id, context):
        await update.message.reply_text(
            f"❗ Подпишись на канал:\n{CHANNEL_USERNAME}\n\n"
            "После подписки нажми /start"
        )
        return

    if user_exists(user_id):
        await update.message.reply_text("❗ Ты уже получал видео.")
        return

    add_user(user_id)

    videos = get_videos()
    if not videos:
        await update.message.reply_text("❗ Видео пока не добавлены.")
        return

    for file_id in videos:
        await update.message.reply_video(file_id)

    await update.message.reply_text("✅ Все видео отправлены!")


async def admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.video:
        return

    save_video(update.message.video.file_id)
    await update.message.reply_text("✅ Видео сохранено.")


# ---------- ЗАПУСК ----------

def main():
    print("Бот запущен 24/7 (polling)")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, admin_video))

    app.run_polling()


if __name__ == "__main__":
    main()
