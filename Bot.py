import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Your Telegram username WITHOUT @
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "silverfoxoftiktok")

# Strongly recommended:
# Add ADMIN_ID to Render Environment Variables.
# Example: 123456789
ADMIN_ID = os.getenv("ADMIN_ID", "")

PORT = int(os.getenv("PORT", "10000"))

# Render gives your service its public URL.
# Add WEBHOOK_URL to Render Environment Variables:
# https://your-service-name.onrender.com
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")

DB_FILE = "bensocial.db"


# ============================================================
# DEFAULT PAYMENT DETAILS
# ============================================================

BANK = "Opay (Paycom)"
ACCOUNT_NAME = "Toluwani Awe"
ACCOUNT_NUMBER = "8165405921"


# ============================================================
# DATABASE
# ============================================================

def db():
    return sqlite3.connect(DB_FILE)


def init_database():
    conn = db()
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
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_key TEXT UNIQUE NOT NULL,
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

    conn.commit()
    conn.close()

    # Add default services only if database is empty
    add_default_services()


def add_default_services():
    conn = db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM services")
    count = cursor.fetchone()[0]

    if count == 0:
        default_services = [
            ("whatsapp", "📱 WhatsApp Number", "₦4,500", "Available"),
            ("textnow", "📲 TextNow", "₦2,200", "Available"),
            ("esim", "🌐 eSIM", "₦25,000", "Available"),
            ("facebook", "📘 Facebook", "₦2,300", "Available"),
            ("twitter", "🐦 Twitter", "₦2,860", "Available"),
            ("usa_facebook", "🇺🇸 USA Facebook", "₦2,200", "35"),
            ("video_tools", "📹 Video Call Tools", "₦56,000", "7"),
            ("telegram_verification",
             "✅ Telegram Verification",
             "₦10,000",
             "9"),
            ("apple", "🍎 Apple iCloud", "₦7,000", "24"),
            ("france_tiktok",
             "🇫🇷 France TikTok",
             "₦1,800",
             "6"),
            ("hma", "🔐 HMA VPN — 1 Month", "₦3,780", "62"),
            ("expressvpn",
             "🔐 ExpressVPN — 1 Month",
             "₦3,800",
             "25"),
            ("instagram",
             "📸 USA Instagram",
             "₦2,300",
             "23"),
            ("tiktok_boost",
             "🎵 TikTok Boost — 1K",
             "₦4,536",
             "Available"),
        ]

        cursor.executemany("""
            INSERT INTO services
            (service_key, name, price, stock)
            VALUES (?, ?, ?, ?)
        """, default_services)

        conn.commit()

    conn.close()


def register_user(user):
    conn = db()
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


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(user):
    # Best method: Telegram numeric ID
    if ADMIN_ID:
        return str(user.id) == str(ADMIN_ID)

    # Fallback to username
    username = (user.username or "").lower().replace("@", "")
    return username == ADMIN_USERNAME.lower().replace("@", "")


async def admin_only(update: Update):
    if not is_admin(update.effective_user):
        if update.message:
            await update.message.reply_text(
                "❌ You are not authorized to use this command."
            )
        return False

    return True


# ============================================================
# SERVICES
# ============================================================

def get_services():
    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT service_key, name, price, stock
        FROM services
        ORDER BY service_id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def get_service(key):
    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT service_key, name, price, stock
        FROM services
        WHERE service_key = ?
    """, (key,))

    row = cursor.fetchone()
    conn.close()

    return row


def services_keyboard():
    buttons = []

    service_items = get_services()

    for i in range(0, len(service_items), 2):
        row = []

        for key, name, price, stock in service_items[i:i + 2]:
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
        text = (
            "🤖 Bensocial Admin Commands\n\n"

            "➕ Add service:\n"
            "/addservice key | name | price | stock\n\n"

            "💰 Change price:\n"
            "/changeprice key | new price\n\n"

            "📦 Change stock:\n"
            "/stock key | new stock\n\n"

            "📋 List services:\n"
            "/services\n\n"

            "🗑 Delete service:\n"
            "/deleteservice key\n\n"

            "💳 Change payment account:\n"
            "/setaccount bank | account name | account number\n\n"

            "👥 Registered users:\n"
            "/users\n\n"

            "🔐 Admin menu:\n"
            "/admin"
        )

    else:
        text = (
            "🤖 Bensocial Bot Help\n\n"
            "/start — Open services\n"
            "/help — Show help\n\n"
            "Choose a service to view its price and availability."
        )

    await update.message.reply_text(text)


# ============================================================
# SERVICE SELECTED
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

    text = (
        f"{name}\n\n"
        f"💰 Price: {price}\n"
        f"📦 Stock: {stock}\n\n"

        "💳 Payment Details\n"
        f"Bank: {BANK}\n"
        f"Account Name: {ACCOUNT_NAME}\n"
        f"Account Number: {ACCOUNT_NUMBER}\n\n"

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
                "⬅️ Back to Services",
                callback_data="back_services"
            )
        ],
    ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard
    )


# ============================================================
# BACK
# ============================================================

async def back_to_services(
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

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await admin_only(update):
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Add Service",
                callback_data="admin_add"
            ),
            InlineKeyboardButton(
                "💰 Change Price",
                callback_data="admin_price"
            )
        ],
        [
            InlineKeyboardButton(
                "📦 Change Stock",
                callback_data="admin_stock"
            ),
            InlineKeyboardButton(
                "📋 Services",
                callback_data="admin_services"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Delete Service",
                callback_data="admin_delete"
            )
        ]
    ])

    await update.message.reply_text(
        "🔐 Bensocial Admin Panel\n\n"
        "You can also use the commands directly.",
        reply_markup=keyboard
    )


# ============================================================
# ADD SERVICE
# ============================================================

async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await admin_only(update):
        return

    text = update.message.text

    parts = text[len("/addservice"):].strip().split("|")

    if len(parts) != 4:
        await update.message.reply_text(
            "❌ Format:\n\n"
            "/addservice key | name | price | stock\n\n"
            "Example:\n"
            "/addservice web_design | 🌐 Website Design | ₦30,000 | 10"
        )
        return

    key, name, price, stock = [
        x.strip() for x in parts
    ]

    if not key.replace("_", "").isalnum():
        await update.message.reply_text(
            "❌ Invalid key.\n\n"
            "Use only letters, numbers and underscores."
        )
        return

    conn = db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO services
            (service_key, name, price, stock)
            VALUES (?, ?, ?, ?)
        """, (
            key,
            name,
            price,
            stock
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()

        await update.message.reply_text(
            "❌ That service key already exists."
        )
        return

    conn.close()

    await update.message.reply_text(
        "✅ Service added successfully!\n\n"
        f"🔑 Key: {key}\n"
        f"🛍️ Name: {name}\n"
        f"💰 Price: {price}\n"
        f"📦 Stock: {stock}"
    )


# ============================================================
# CHANGE PRICE
# ============================================================

async def change_price(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await admin_only(update):
        return

    parts = update.message.text[len("/changeprice"):].strip().split("|")

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Format:\n\n"
            "/changeprice key | new price\n\n"
            "Example:\n"
            "/changeprice whatsapp | ₦5,000"
        )
        return

    key, new_price = [
        x.strip() for x in parts
    ]

    service = get_service(key)

    if not service:
        await update.message.reply_text(
            "❌ Service not found."
        )
        return

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET price = ?
        WHERE service_key = ?
    """, (
        new_price,
        key
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Price updated successfully!\n\n"
        f"🛍️ {service[1]}\n"
        f"💰 New price: {new_price}"
    )


# ============================================================
# STOCK
# ============================================================

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await admin_only(update):
        return

    parts = update.message.text[len("/stock"):].strip().split("|")

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Format:\n\n"
            "/stock key | new stock\n\n"
            "Example:\n"
            "/stock whatsapp | 20"
        )
        return

    key, new_stock = [
        x.strip() for x in parts
    ]

    service = get_service(key)

    if not service:
        await update.message.reply_text(
            "❌ Service not found."
        )
        return

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET stock = ?
        WHERE service_key = ?
    """, (
        new_stock,
        key
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Stock updated successfully!\n\n"
        f"🛍️ {service[1]}\n"
        f"📦 New stock: {new_stock}"
    )


# ============================================================
# LIST SERVICES
# ============================================================

async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await admin_only(update):
        return

    services = get_services()

    if not services:
        await update.message.reply_text(
            "📭 No services available."
        )
        return

    lines = ["📋 Bensocial Services\n"]

    for key, name, price, stock in services:
        lines.append(
            f"🔑 {key}\n"
            f"   {name}\n"
            f"   💰 {price}\n"
            f"   📦 Stock: {stock}\n"
        )

    await update.message.reply_text(
        "\n".join(lines)
    )


# ============================================================
# DELETE SERVICE
# ============================================================

async def delete_service(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await admin_only(update):
        return

    key = update.message.text[len("/deleteservice"):].strip()

    if not key:
        await update.message.reply_text(
            "❌ Format:\n"
            "/deleteservice key"
        )
        return

    service = get_service(key)

    if not service:
        await update.message.reply_text(
            "❌ Service not found."
        )
        return

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM services
        WHERE service_key = ?
    """, (key,))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Service deleted.\n\n"
        f"🗑 {service[1]}"
    )


# ============================================================
# PAYMENT DETAILS
# ============================================================

async def set_account(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global BANK
    global ACCOUNT_NAME
    global ACCOUNT_NUMBER

    if not await admin_only(update):
        return

    parts = update.message.text[len("/setaccount"):].strip().split("|")

    if len(parts) != 3:
        await update.message.reply_text(
            "❌ Format:\n\n"
            "/setaccount bank | account name | account number\n\n"
            "Example:\n"
            "/setaccount Opay | Bensocial | 1234567890"
        )
        return

    bank, account_name, account_number = [
        x.strip() for x in parts
    ]

    BANK = bank
    ACCOUNT_NAME = account_name
    ACCOUNT_NUMBER = account_number

    await update.message.reply_text(
        "✅ Payment details updated!\n\n"
        f"🏦 Bank: {BANK}\n"
        f"👤 Account Name: {ACCOUNT_NAME}\n"
        f"💳 Account Number: {ACCOUNT_NUMBER}"
    )


# ============================================================
# USERS
# ============================================================

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await admin_only(update):
        return

    conn = db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

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
    await query.answer()

    if not is_admin(query.from_user):
        await query.answer(
            "❌ Not authorized.",
            show_alert=True
        )
        return

    action = query.data

    if action == "admin_services":

        services = get_services()

        if not services:
            await query.edit_message_text(
                "📭 No services."
            )
            return

        lines = ["📋 Services\n"]

        for key, name, price, stock in services:
            lines.append(
                f"🔑 {key}\n"
                f"{name}\n"
                f"💰 {price}\n"
                f"📦 {stock}\n"
            )

        await query.edit_message_text(
            "\n".join(lines)
        )
        return

    instructions = {
        "admin_add":
            "➕ Add Service\n\n"
            "/addservice key | name | price | stock\n\n"
            "Example:\n"
            "/addservice web_design | 🌐 Website Design | ₦30,000 | 10",

        "admin_price":
            "💰 Change Price\n\n"
            "/changeprice key | new price\n\n"
            "Example:\n"
            "/changeprice whatsapp | ₦5,000",

        "admin_stock":
            "📦 Change Stock\n\n"
            "/stock key | new stock\n\n"
            "Example:\n"
            "/stock whatsapp | 20",

        "admin_delete":
            "🗑 Delete Service\n\n"
            "/deleteservice key\n\n"
            "Example:\n"
            "/deleteservice web_design",
    }

    await query.edit_message_text(
        instructions.get(
            action,
            "Use /admin to open the admin panel."
        )
    )


# ============================================================
# NORMAL MESSAGES
# ============================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    register_user(update.effective_user)

    await update.message.reply_text(
        "💬 Please choose a service:",
        reply_markup=services_keyboard()
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update, context):
    print("BOT ERROR:", context.error)


# ============================================================
# MAIN — RENDER WEBHOOK
# ============================================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    if not WEBHOOK_URL:
        raise RuntimeError(
            "WEBHOOK_URL environment variable is missing."
        )

    init_database()

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
        CommandHandler("addservice", add_service)
    )

    app.add_handler(
        CommandHandler("changeprice", change_price)
    )

    app.add_handler(
        CommandHandler("stock", stock_command)
    )

    app.add_handler(
        CommandHandler("services", services_command)
    )

    app.add_handler(
        CommandHandler("deleteservice", delete_service)
    )

    app.add_handler(
        CommandHandler("setaccount", set_account)
    )

    app.add_handler(
        CommandHandler("users", users_command)
    )

    # Service buttons
    app.add_handler(
        CallbackQueryHandler(
            service_selected,
            pattern=r"^service:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            back_to_services,
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
            handle_message
        )
    )

    app.add_error_handler(error_handler)

    print("Bensocial Bot starting with webhook...")
    print(f"Port: {PORT}")
    print(f"Webhook: {WEBHOOK_URL}")

    # IMPORTANT:
    # Webhook mode is used instead of run_polling().
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
