import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "silverfoxoftiktok"
).lstrip("@")

PORT = int(os.getenv("PORT", "10000"))

DB_FILE = "bensocial.db"


# ============================================================
# DEFAULT PAYMENT DETAILS
# ============================================================

DEFAULT_BANK = "Opay (Paycom)"
DEFAULT_ACCOUNT_NAME = "Toluwani Awe"
DEFAULT_ACCOUNT_NUMBER = "8165405921"


# ============================================================
# DEFAULT SERVICES
# ============================================================

DEFAULT_SERVICES = [
    ("whatsapp", "📱 WhatsApp Number", "₦4,500", "Available"),
    ("textnow", "📲 TextNow", "₦2,200", "Available"),
    ("esim", "🌐 eSIM", "₦25,000", "Available"),
    ("facebook", "📘 Facebook", "₦2,300", "Available"),
    ("twitter", "🐦 Twitter/X", "₦2,860", "Available"),
    ("usa_facebook", "🇺🇸 USA Facebook", "₦2,200", "35"),
    ("video_tools", "📹 Video Call Tools", "₦56,000", "7"),
    (
        "telegram_verification",
        "✅ Telegram Verification",
        "₦10,000",
        "9",
    ),
    ("apple", "🍎 Apple iCloud", "₦7,000", "24"),
    ("france_tiktok", "🇫🇷 France TikTok", "₦1,800", "6"),
    ("hma", "🔐 HMA VPN — 1 Month", "₦3,780", "62"),
    (
        "expressvpn",
        "🔐 ExpressVPN — 1 Month",
        "₦3,800",
        "25",
    ),
    ("instagram", "📸 USA Instagram", "₦2,300", "23"),
    (
        "tiktok_boost",
        "🎵 TikTok Followers — 1K",
        "₦4,536",
        "Available",
    ),
]


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return sqlite3.connect(DB_FILE)


def init_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            service_key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price TEXT NOT NULL,
            stock TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Add default services if they don't exist.
    for service in DEFAULT_SERVICES:
        cursor.execute("""
            INSERT OR IGNORE INTO services
            (service_key, name, price, stock)
            VALUES (?, ?, ?, ?)
        """, service)

    # Add default payment settings.
    defaults = {
        "bank": DEFAULT_BANK,
        "account_name": DEFAULT_ACCOUNT_NAME,
        "account_number": DEFAULT_ACCOUNT_NUMBER,
    }

    for key, value in defaults.items():
        cursor.execute("""
            INSERT OR IGNORE INTO settings
            (key, value)
            VALUES (?, ?)
        """, (key, value))

    conn.commit()
    conn.close()


def register_user(user):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username or "",
        user.first_name or "",
    ))

    conn.commit()
    conn.close()


def get_setting(key):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT value FROM settings WHERE key = ?",
        (key,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]

    return ""


def set_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO settings
        (key, value)
        VALUES (?, ?)
    """, (key, value))

    conn.commit()
    conn.close()


def get_services():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT service_key, name, price, stock
        FROM services
        ORDER BY rowid ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_service(key):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT service_key, name, price, stock
        FROM services
        WHERE service_key = ?
    """, (key,))

    row = cursor.fetchone()
    conn.close()

    return row


# ============================================================
# ADMIN
# ============================================================

def is_admin(user):
    if not user:
        return False

    username = (user.username or "").lstrip("@").lower()

    return username == ADMIN_USERNAME.lower()


async def check_admin(update):
    if not is_admin(update.effective_user):
        if update.message:
            await update.message.reply_text(
                "❌ Admin access only."
            )
        return False

    return True


# ============================================================
# CUSTOMER MENU
# ============================================================

def services_keyboard():
    services = get_services()

    buttons = []

    for i in range(0, len(services), 2):
        row = []

        for key, name, price, stock in services[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    name,
                    callback_data=f"service:{key}"
                )
            )

        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            "💬 Contact Admin",
            url=f"https://t.me/{ADMIN_USERNAME}"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    await update.message.reply_text(
        "👋 Welcome to Bensocial Bot!\n\n"
        "✅ You have been registered successfully.\n\n"
        "🛍️ Choose a service below:",
        reply_markup=services_keyboard()
    )


# ============================================================
# HELP
# ============================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user):
        await update.message.reply_text(
            "🔐 ADMIN COMMANDS\n\n"
            "/admin — Admin menu\n"
            "/addservice — Add service\n"
            "/changeprice — Change price\n"
            "/stock — Change stock\n"
            "/services — View services\n"
            "/deleteservice — Delete service\n"
            "/setbank — Change bank\n"
            "/setaccountname — Change account name\n"
            "/setaccountnumber — Change account number\n"
            "/paymentinfo — View payment details\n"
            "/users — View registered users\n"
        )
    else:
        await update.message.reply_text(
            "🤖 Bensocial Bot\n\n"
            "/start — Open services\n"
            "/help — Show help"
        )


# ============================================================
# SERVICE SELECTION
# ============================================================

async def service_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    key = query.data.replace("service:", "")

    service = get_service(key)

    if not service:
        await query.edit_message_text(
            "❌ Service not found."
        )
        return

    _, name, price, stock = service

    bank = get_setting("bank")
    account_name = get_setting("account_name")
    account_number = get_setting("account_number")

    text = (
        f"{name}\n\n"
        f"💰 Price: {price}\n"
        f"📦 Stock: {stock}\n\n"
        "💳 PAYMENT DETAILS\n"
        f"Bank: {bank}\n"
        f"Account Name: {account_name}\n"
        f"Account Number: {account_number}\n\n"
        "After payment, contact the admin with your "
        "payment receipt/order details."
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💬 Contact Admin",
                url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="back_services"
            )
        ],
    ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard
    )


async def back_services(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🛍️ Choose a service:",
        reply_markup=services_keyboard()
    )


# ============================================================
# ADMIN MENU
# ============================================================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Add Service",
                callback_data="admin_add"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Change Price",
                callback_data="admin_price"
            ),
            InlineKeyboardButton(
                "📦 Change Stock",
                callback_data="admin_stock"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 Services",
                callback_data="admin_services"
            ),
            InlineKeyboardButton(
                "💳 Payment",
                callback_data="admin_payment"
            )
        ],
    ])

    await update.message.reply_text(
        "🔐 BENSOCIAL ADMIN PANEL\n\n"
        "Choose an option or use the commands.",
        reply_markup=keyboard
    )


# ============================================================
# ADD SERVICE
# ============================================================

async def addservice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [x.strip() for x in raw.split("|")]

    if len(parts) != 4:
        await update.message.reply_text(
            "❌ Correct format:\n\n"
            "/addservice key | name | price | stock\n\n"
            "Example:\n"
            "/addservice snapchat | 👻 Snapchat | ₦3,000 | 10"
        )
        return

    key, name, price, stock = parts

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO services
            (service_key, name, price, stock)
            VALUES (?, ?, ?, ?)
        """, (key, name, price, stock))

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()

        await update.message.reply_text(
            "❌ That service key already exists."
        )
        return

    conn.close()

    await update.message.reply_text(
        "✅ SERVICE ADDED\n\n"
        f"🔑 Key: {key}\n"
        f"🛍️ Name: {name}\n"
        f"💰 Price: {price}\n"
        f"📦 Stock: {stock}"
    )


# ============================================================
# CHANGE PRICE
# ============================================================

async def changeprice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [x.strip() for x in raw.split("|")]

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Correct format:\n\n"
            "/changeprice key | new price\n\n"
            "Example:\n"
            "/changeprice whatsapp | ₦5,000"
        )
        return

    key, price = parts

    if not get_service(key):
        await update.message.reply_text(
            "❌ Service not found."
        )
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET price = ?
        WHERE service_key = ?
    """, (price, key))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ PRICE UPDATED\n\n"
        f"🔑 {key}\n"
        f"💰 New price: {price}"
    )


# ============================================================
# STOCK
# ============================================================

async def stock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [x.strip() for x in raw.split("|")]

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Correct format:\n\n"
            "/stock key | new stock\n\n"
            "Example:\n"
            "/stock whatsapp | 20"
        )
        return

    key, new_stock = parts

    if not get_service(key):
        await update.message.reply_text(
            "❌ Service not found."
        )
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET stock = ?
        WHERE service_key = ?
    """, (new_stock, key))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ STOCK UPDATED\n\n"
        f"🔑 {key}\n"
        f"📦 New stock: {new_stock}"
    )


# ============================================================
# SERVICES LIST
# ============================================================

async def services_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    services = get_services()

    if not services:
        await update.message.reply_text(
            "📭 No services found."
        )
        return

    lines = ["📋 BENSOCIAL SERVICES\n"]

    for key, name, price, stock in services:
        lines.append(
            f"🔑 {key}\n"
            f"{name}\n"
            f"💰 {price}\n"
            f"📦 {stock}\n"
        )

    await update.message.reply_text(
        "\n".join(lines)
    )


# ============================================================
# DELETE SERVICE
# ============================================================

async def deleteservice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    key = update.message.text.partition(" ")[2].strip()

    if not key:
        await update.message.reply_text(
            "❌ Example:\n"
            "/deleteservice snapchat"
        )
        return

    service = get_service(key)

    if not service:
        await update.message.reply_text(
            "❌ Service not found."
        )
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM services
        WHERE service_key = ?
    """, (key,))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🗑️ Deleted:\n{service[1]}"
    )


# ============================================================
# PAYMENT SETTINGS
# ============================================================

async def setbank(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    value = update.message.text.partition(" ")[2].strip()

    if not value:
        await update.message.reply_text(
            "Example:\n/setbank Opay (Paycom)"
        )
        return

    set_setting("bank", value)

    await update.message.reply_text(
        f"✅ Bank updated to:\n{value}"
    )


async def setaccountname(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    value = update.message.text.partition(" ")[2].strip()

    if not value:
        await update.message.reply_text(
            "Example:\n/setaccountname Bensocial"
        )
        return

    set_setting("account_name", value)

    await update.message.reply_text(
        f"✅ Account name updated to:\n{value}"
    )


async def setaccountnumber(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    value = update.message.text.partition(" ")[2].strip()

    if not value:
        await update.message.reply_text(
            "Example:\n/setaccountnumber 1234567890"
        )
        return

    set_setting("account_number", value)

    await update.message.reply_text(
        f"✅ Account number updated to:\n{value}"
    )


async def paymentinfo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    await update.message.reply_text(
        "💳 CURRENT PAYMENT DETAILS\n\n"
        f"Bank: {get_setting('bank')}\n"
        f"Account Name: {get_setting('account_name')}\n"
        f"Account Number: {get_setting('account_number')}"
    )


# ============================================================
# USERS
# ============================================================

async def users_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await check_admin(update):
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    count = cursor.fetchone()[0]

    conn.close()

    await update.message.reply_text(
        f"👥 Registered users: {count}"
    )


# ============================================================
# ADMIN BUTTONS
# ============================================================

async def admin_buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if not is_admin(query.from_user):
        await query.answer(
            "❌ Admin only.",
            show_alert=True
        )
        return

    await query.answer()

    action = query.data

    if action == "admin_add":
        await query.message.reply_text(
            "➕ ADD SERVICE\n\n"
            "/addservice key | name | price | stock\n\n"
            "Example:\n"
            "/addservice snapchat | 👻 Snapchat | ₦3,000 | 10"
        )

    elif action == "admin_price":
        await query.message.reply_text(
            "💰 CHANGE PRICE\n\n"
            "/changeprice key | new price\n\n"
            "Example:\n"
            "/changeprice whatsapp | ₦5,000"
        )

    elif action == "admin_stock":
        await query.message.reply_text(
            "📦 CHANGE STOCK\n\n"
            "/stock key | new stock\n\n"
            "Example:\n"
            "/stock whatsapp | 20"
        )

    elif action == "admin_services":
        services = get_services()

        text = "📋 SERVICES\n\n"

        for key, name, price, stock in services:
            text += (
                f"{key}\n"
                f"{name}\n"
                f"💰 {price}\n"
                f"📦 {stock}\n\n"
            )

        await query.message.reply_text(text)

    elif action == "admin_payment":
        await query.message.reply_text(
            "💳 PAYMENT SETTINGS\n\n"
            f"Bank: {get_setting('bank')}\n"
            f"Account Name: {get_setting('account_name')}\n"
            f"Account Number: {get_setting('account_number')}\n\n"
            "Change them with:\n"
            "/setbank\n"
            "/setaccountname\n"
            "/setaccountnumber"
        )


# ============================================================
# NORMAL TEXT
# ============================================================

async def normal_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    register_user(update.effective_user)

    await update.message.reply_text(
        "🛍️ Choose a service:",
        reply_markup=services_keyboard()
    )


# ============================================================
# RENDER HEALTH SERVER
# ============================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain"
        )
        self.end_headers()

        self.wfile.write(
            b"Bensocial Bot is online"
        )

    def log_message(self, format, *args):
        return


def start_health_server():
    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"Health server running on port {PORT}"
    )

    server.serve_forever()


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    init_database()

    # Start Render health server in background.
    health_thread = threading.Thread(
        target=start_health_server,
        daemon=True
    )

    health_thread.start()

    # Build Telegram application.
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Customer commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    # Admin commands
    app.add_handler(
        CommandHandler("admin", admin_command)
    )

    app.add_handler(
        CommandHandler("addservice", addservice)
    )

    app.add_handler(
        CommandHandler("changeprice", changeprice)
    )

    app.add_handler(
        CommandHandler("stock", stock)
    )

    app.add_handler(
        CommandHandler("services", services_command)
    )

    app.add_handler(
        CommandHandler("deleteservice", deleteservice)
    )

    app.add_handler(
        CommandHandler("setbank", setbank)
    )

    app.add_handler(
        CommandHandler("setaccountname", setaccountname)
    )

    app.add_handler(
        CommandHandler(
            "setaccountnumber",
            setaccountnumber
        )
    )

    app.add_handler(
        CommandHandler(
            "paymentinfo",
            paymentinfo
        )
    )

    app.add_handler(
        CommandHandler(
            "users",
            users_command
        )
    )

    # Customer buttons
    app.add_handler(
        CallbackQueryHandler(
            service_selected,
            pattern=r"^service:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            back_services,
            pattern=r"^back_services$"
        )
    )

    # Admin buttons
    app.add_handler(
        CallbackQueryHandler(
            admin_buttons,
            pattern=r"^admin_"
        )
    )

    # Normal messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            normal_message
        )
    )

    print("Bensocial Bot is starting...")
    print("Telegram polling enabled.")

    # Only ONE polling instance should run.
    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
