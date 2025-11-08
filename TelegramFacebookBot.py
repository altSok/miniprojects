import os
import requests
from functools import wraps
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

APP_ID = "GRAPH_APP_ID"
APP_SECRET = "GRAPH_APP_SECRET"
OWNER_ID = int(os.getenv("OWNER_ID", "OWNER_BOT_ID")) # id владельца бота
TELEGRAM_TOKEN = "BOT_TOKEN" # токен бота
GRAPH_API_BASE = "https://graph.facebook.com/v24.0" # При смене версии Graph Api обязательно поменять /v24.0

TOKEN_FILE = "token.txt" # Файл в который сохраняются указанные API
PAGE_ACCESS_WAIT_TOKEN = "wait_for_page_token"

PAGE_ID_FILE = "page_id.txt"
PAGE_ID_WAIT_TOKEN = "wait_for_page_id"


# Декоратор для проверки пользователь = владелец
def only_owner(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or user.id != OWNER_ID:
            await update.message.reply_text("У тебя нет прав использовать этого бота.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def save_page_id(page_id: str):
    with open(PAGE_ID_FILE, "w", encoding="utf8") as f:
        f.write(page_id)

def load_page_id():
    if os.path.exists(PAGE_ID_FILE):
        with open(PAGE_ID_FILE, "r", encoding="utf8") as f:
            return f.read().strip()
    return ""

def load_page_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf8") as f:
            return f.read().strip()
    return ""

def save_page_token(token: str):
    with open(TOKEN_FILE, "w", encoding="utf8") as f:
        f.write(token)

PAGE_ACCESS_TOKEN = load_page_token()
PAGE_ID = load_page_id()

def try_get_page_token_from_user_token(user_token: str, page_id: str):
    try:
        r = requests.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={"access_token": user_token},
            timeout=10
        )
        if not r.ok:
            return None

        data = r.json()
        for page in data.get("data", []):
            if str(page.get("id")) == str(page_id):
                return page.get("access_token")
    except Exception:
        return None
    return None


def validate_page_token_for_page(page_token: str, page_id: str) -> bool:
    """Проверяет, подходит ли page token к странице PAGE_ID"""
    try:
        r = requests.get(
            f"{GRAPH_API_BASE}/{PAGE_ID}",
            params={"access_token": page_token},
            timeout=10
        )
        if not r.ok:
            return False

        return str(r.json().get("id")) == str(page_id)
    except Exception:
        return False

def exchange_for_long_lived(user_token: str):
    try:
        url = f"{GRAPH_API_BASE}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "fb_exchange_token": user_token
        }
        r = requests.get(url, params=params, timeout=10)

        if not r.ok:
            return None

        data = r.json()
        return data.get("access_token")  # long-lived user token
    except Exception:
        return None

# СПИСОК КОМАНД БОТА

@only_owner
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Присылай текст или фото — я опубликую это на твою Facebook Page.\n"
        "Чтобы обновить токен, используй /api"
    )

@only_owner
async def api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop(PAGE_ACCESS_WAIT_TOKEN, None)
    context.user_data[PAGE_ACCESS_WAIT_TOKEN] = True
    await update.message.reply_text(
        "Отправь PAGE_ACCESS_TOKEN или USER_TOKEN.\n"
        "Чтобы отменить — /cancel")

@only_owner
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop(PAGE_ACCESS_WAIT_TOKEN, None)
    await update.message.reply_text("❌ Операция отменена. Отправьте текст и/или фото для публикации поста")

@only_owner
async def pageid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop(PAGE_ID_WAIT_TOKEN, None)
    context.user_data[PAGE_ID_WAIT_TOKEN] = True
    await update.message.reply_text(
        "Отправь ID Страницы фейсбука на которую мы будем постить.\n"
        "Чтобы отменить — /cancel")

@only_owner
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Список доступных команд:\n"
                                        "/start\n"
                                        "/api (Подключение PAGE_ACCESS_TOKEN)\n"
                                        "/getlink (Ссылка перейдя по которой вы сможете легко получить ваш PAGE_ACCESS_TOKEN\n"
                                        "/page_id (Подключение страницы Facebook Page ID)\n"
                                        "/cancel (Отмена крайнего действия)")




# Ожидание ввода токенов
@only_owner
async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if context.user_data.get(PAGE_ID_WAIT_TOKEN):
        global PAGE_ACCESS_TOKEN
        global PAGE_ID

        if not text.isdigit():
            await update.message.reply_text("❌ PAGE_ID должен содержать только цифры.")
            return

        if not PAGE_ACCESS_WAIT_TOKEN:
            await update.message.reply_text("❗ Сначала установите токен через /api")
            return

        r = requests.get(
            f"{GRAPH_API_BASE}/{text}",
            params={"access_token": PAGE_ACCESS_TOKEN}
        )

        if not r.ok:
            await update.message.reply_text("❌ Неверный PAGE_ID или нет доступа.")
            return

        PAGE_ID = text
        context.user_data.pop(PAGE_ID_WAIT_TOKEN, None)
        await update.message.reply_text(f"✅ PAGE_ID установлен: {PAGE_ID}")
        return

    if context.user_data.get(PAGE_ACCESS_WAIT_TOKEN):


        await update.message.reply_text("🔎 Проверяю токен...")

        new_token = text

        PAGE_ACCESS_TOKEN = new_token
        context.user_data.pop(PAGE_ACCESS_WAIT_TOKEN, None)
        await update.message.reply_text("✅ Токен сохранён.")
        return
    await handle_text(update, context)

# Публикация текста
@only_owner
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if not PAGE_ACCESS_TOKEN:
        await update.message.reply_text("❗ Сначала установи токен /api")
        return

    r = requests.post(
        f"{GRAPH_API_BASE}/{PAGE_ID}/feed",
        data={"message": text, "access_token": PAGE_ACCESS_TOKEN}
    )

    if r.ok:
        await update.message.reply_text("✅ Пост опубликован.")
    else:
        await update.message.reply_text(f"❌ Ошибка: {r.text}")



# Публикация фото
@only_owner
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not PAGE_ACCESS_TOKEN:
        await update.message.reply_text("❗ Сначала установи токен /api")
        return

    caption = update.message.caption or ""
    photo = update.message.photo[-1]
    file = await photo.get_file()
    local_path = f"{photo.file_id}.jpg"
    await file.download_to_drive(local_path)

    with open(local_path, "rb") as f:
        r = requests.post(
            f"{GRAPH_API_BASE}/{PAGE_ID}/photos",
            files={"source": f},
            data={"message": caption, "access_token": PAGE_ACCESS_TOKEN}
        )

    os.remove(local_path)

    if r.ok:
        await update.message.reply_text("✅ Фото опубликовано.")
    else:
        await update.message.reply_text(f"❌ Ошибка FB: {r.text}")


# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("api", api))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("page_id", pageid))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_inputs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("✅ Bot started")
    app.run_polling()