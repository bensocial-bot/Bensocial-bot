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

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "silverfoxoftiktok"
).lstrip("@").lower()

DB_FILE = "bensocial.db"


# =========================
# DEFAULT SERVICES
# =========================

DEFAULT_SERVICES = {
    "whatsapp": {
        "name": "📱 WhatsApp Number",
        "price": "₦4,500",
        "stock": "Available",
    },
    "textnow": {
        "name": "📲 TextNow",
        "price": "₦2,200",
        "stock": "Available",
    },
    "esim": {
        "name": "🌐 eSIM",
        "price": "₦25,000",
        "stock": "Available",
    },
    "facebook": {
        "name": "📘 Facebook",
        "price": "₦2,300",
        "stock": "Available",
    },
    "twitter": {
        "name": "🐦 Twitter",
        "price": "₦2,860",
        "stock": "Available",
    },
    "usa_facebook": {
        "name": "🇺🇸 USA Facebook",
        "price": "₦2,200",
        "stock": "35",
    },
    "video_tools": {
        "name": "📹 2026 Video Call Tools",
        "price": "₦56,000",
        "stock": "7",
    },
    "telegram_verification": {
        "name": "✅ Telegram Verification",
        "price": "₦10,000",
        "stock": "9",
    },
    "apple": {
        "name": "🍎 Apple iCloud",
        "price": "₦7,000",
        "stock": "24",
    },
    "france_tiktok": {
        "name": "🇫🇷 France TikTok",
        "price": "₦1,800",
        "stock": "6",
    },
    "hma": {
        "name": "🔐 HMA VPN — 1 Month",
        "price": "₦3,780",
        "stock": "62",
    },
    "expressvpn": {
        "name": "🔐 ExpressVPN — 1 Month",
        "price": "₦3,800",
        "stock": "25",
    },
    "instagram": {
        "name": "📸 USA Instagram",
        "price": "₦2,300",
        "stock": "23",
    },
}


# =========================
# DATABASE
# =========================

def get_db():
    return sqlite3.connect(DB_FILE)


def init_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price TEXT NOT NULL,
            stock TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    for key, service in DEFAULT_SERVICES.items():
        cursor.execute("""
            INSERT OR IGNORE INTO services
            (key, name, price, stock)
            VALUES (?, ?, ?, ?)
        """, (
            key,
            service["name"],
            service["price"],
            service["stock"],
        ))

    defaults = {
        "bank": "Opay (Paycom)",
        "account_name": "Toluwani Awe",
        "account_number": "8165405921",
    }

    for key, value in defaults.items():
        cursor.execute("""
            INSERT OR IGNORE INTO settings
            (key, value)
            VALUES (?, ?)
        """, (key, value))

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

    return result[0] if result else ""


def set_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (key, value))

    conn.commit()
    conn.close()


def get_services():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key, name, price, stock
        FROM services
        ORDER BY rowid
    """)

    rows = cursor.fetchall()
    conn.close()

    return {
        row[0]: {
            "name": row[1],
            "price": row[2],
            "stock": row[3],
        }
        for row in rows
    }


def get_service(key):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key, name, price, stock
        FROM services
        WHERE key = ?
    """, (key,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "key": row[0],
        "name": row[1],
        "price": row[2],
        "stock": row[3],
    }


# =========================
# ADMIN SECURITY
# =========================

def is_admin(update: Update):
    user = update.effective_user

    if not user:
        return False

    username = (user.username or "").lower()

    return username == ADMIN_USERNAME


async def admin_only(update: Update):

    if not is_admin(update):
        if update.message:
            await update.message.reply_text(
                "⛔ Admin only."
            )
        return False

    return True


# =========================
# CUSTOMER MENU
# =========================

def services_keyboard():

    buttons = []

    services = list(get_services().items())

    for i in range(0, len(services), 2):

        row = []

        for key, service in services[i:i + 2]:

            row.append(
                InlineKeyboardButton(
                    service["name"],
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


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "👋 Welcome to Bensocial Bot!\n\n"
        "🛍️ Choose a service below:",
        reply_markup=services_keyboard()
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🤖 Bensocial Bot\n\n"
        "/start — Open services\n"
        "/help — Help"
    )


# =========================
# SERVICE DETAILS
# =========================

async def service_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    key = query.data.replace(
        "service:",
        "",
        1
    )

    service = get_service(key)

    if not service:

        await query.edit_message_text(
            "❌ Service not found."
        )

        return

    bank = get_setting("bank")
    account_name = get_setting("account_name")
    account_number = get_setting("account_number")

    text = (
        f"{service['name']}\n\n"
        f"💰 Price: {service['price']}\n"
        f"📦 Stock: {service['stock']}\n\n"
        "💳 Payment Details\n"
        f"Bank: {bank}\n"
        f"Account Name: {account_name}\n"
        f"Account Number: {account_number}\n\n"
        "After payment, contact the admin "
        "with your payment receipt/order details."
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
        ]
    ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard
    )


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


# =========================
# ADMIN MENU
# =========================

async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    await update.message.reply_text(
        "🔐 BENSOCIAL ADMIN\n\n"

        "➕ ADD SERVICE\n"
        "/addservice key | name | price | stock\n\n"

        "💰 CHANGE PRICE\n"
        "/changeprice key | new price\n\n"

        "📦 CHANGE STOCK\n"
        "/stock key | new stock\n\n"

        "📋 LIST SERVICES\n"
        "/services\n\n"

        "🗑️ DELETE SERVICE\n"
        "/deleteservice key\n\n"

        "💳 CHANGE PAYMENT ACCOUNT\n"
        "/changeaccount\n"
        "Account Number: 6550518571\n"
        "Bank: OPay\n"
        "Account Name: TOLUWANI BENJAMIN/Bensocial\n\n"

        "🔎 PAYMENT INFO\n"
        "/paymentinfo"
    )


# =========================
# ADD SERVICE
# =========================

async def add_service(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    raw = update.message.text.partition(" ")[2].strip()

    parts = [
        part.strip()
        for part in raw.split("|")
    ]

    if len(parts) != 4:

        await update.message.reply_text(
            "❌ Format:\n\n"
            "/addservice key | name | price | stock\n\n"
            "Example:\n"
            "/addservice "
            "tiktok_followers | "
            "🎵 TikTok Followers | "
            "₦4,536/1k | "
            "Available"
        )

        return

    key, name, price, stock = parts

    if not all(
        character.isalnum() or character == "_"
        for character in key
    ):

        await update.message.reply_text(
            "❌ Key can only contain "
            "letters, numbers and underscores."
        )

        return

    conn = get_db()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO services
            (key, name, price, stock)
            VALUES (?, ?, ?, ?)
        """, (
            key.lower(),
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
        "✅ Service added!\n\n"
        f"🔑 Key: {key.lower()}\n"
        f"📌 Name: {name}\n"
        f"💰 Price: {price}\n"
        f"📦 Stock: {stock}"
    )


# =========================
# CHANGE PRICE
# =========================

async def change_price(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    raw = update.message.text.partition(" ")[2].strip()

    parts = [
        part.strip()
        for part in raw.split("|")
    ]

    if len(parts) != 2:

        await update.message.reply_text(
            "❌ Format:\n\n"
            "/changeprice key | new price\n\n"
            "Example:\n"
            "/changeprice whatsapp | ₦5,000"
        )

        return

    key, price = parts

    service = get_service(key.lower())

    if not service:

        await update.message.reply_text(
            "❌ Service not found."
        )

        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET price = ?
        WHERE key = ?
    """, (
        price,
        key.lower()
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Price updated!\n\n"
        f"{service['name']}\n"
        f"💰 New price: {price}"
    )


# =========================
# CHANGE STOCK
# =========================

async def change_stock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    raw = update.message.text.partition(" ")[2].strip()

    parts = [
        part.strip()
        for part in raw.split("|")
    ]

    if len(parts) != 2:

        await update.message.reply_text(
            "❌ Format:\n\n"
            "/stock key | new stock\n\n"
            "Example:\n"
            "/stock whatsapp | 20"
        )

        return

    key, stock = parts

    service = get_service(key.lower())

    if not service:

        await update.message.reply_text(
            "❌ Service not found."
        )

        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET stock = ?
        WHERE key = ?
    """, (
        stock,
        key.lower()
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ Stock updated!\n\n"
        f"{service['name']}\n"
        f"📦 New stock: {stock}"
    )


# =========================
# LIST SERVICES
# =========================

async def list_services(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    services = get_services()

    if not services:

        await update.message.reply_text(
            "📋 No services."
        )

        return

    text = "📋 BENSOCIAL SERVICES\n\n"

    for key, service in services.items():

        text += (
            f"🔑 {key}\n"
            f"{service['name']}\n"
            f"💰 {service['price']}\n"
            f"📦 {service['stock']}\n\n"
        )

    await update.message.reply_text(text)


# =========================
# DELETE SERVICE
# =========================

async def delete_service(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    key = update.message.text.partition(
        " "
    )[2].strip().lower()

    if not key:

        await update.message.reply_text(
            "❌ Example:\n"
            "/deleteservice whatsapp"
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

    cursor.execute(
        "DELETE FROM services WHERE key = ?",
        (key,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🗑️ Deleted:\n{service['name']}"
    )


# =========================
# CHANGE ACCOUNT
# =========================

async def change_account(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    message = update.message.text

    # Remove /changeaccount
    content = message.partition(
        "\n"
    )[2].strip()

    # Also support one-line format
    if not content:

        content = message.partition(
            " "
        )[2].strip()

    account_number = ""
    bank = ""
    account_name = ""

    # Multi-line format
    for line in content.splitlines():

        if ":" not in line:
            continue

        label, value = line.split(
            ":",
            1
        )

        label = label.strip().lower()
        value = value.strip()

        if label in (
            "account number",
            "account_number",
            "number"
        ):
            account_number = value

        elif label == "bank":
            bank = value

        elif label in (
            "account name",
            "account_name",
            "name"
        ):
            account_name = value

    # One-line format:
    # /changeaccount number | bank | name
    if not (
        account_number
        and bank
        and account_name
    ):

        parts = [
            part.strip()
            for part in content.split("|")
        ]

        if len(parts) == 3:

            account_number = parts[0]
            bank = parts[1]
            account_name = parts[2]

    if not (
        account_number
        and bank
        and account_name
    ):

        await update.message.reply_text(
            "❌ Use this format:\n\n"

            "/changeaccount\n"
            "Account Number: 6550518571\n"
            "Bank: OPay\n"
            "Account Name: TOLUWANI BENJAMIN/Bensocial\n\n"

            "OR:\n\n"

            "/changeaccount "
            "6550518571 | "
            "OPay | "
            "TOLUWANI BENJAMIN/Bensocial"
        )

        return

    set_setting(
        "account_number",
        account_number
    )

    set_setting(
        "bank",
        bank
    )

    set_setting(
        "account_name",
        account_name
    )

    await update.message.reply_text(
        "✅ PAYMENT ACCOUNT UPDATED!\n\n"
        f"🏦 Bank: {bank}\n"
        f"👤 Account Name: {account_name}\n"
        f"💳 Account Number: {account_number}"
    )


# =========================
# PAYMENT INFO
# =========================

async def payment_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await admin_only(update):
        return

    await update.message.reply_text(
        "💳 CURRENT PAYMENT DETAILS\n\n"
        f"🏦 Bank: {get_setting('bank')}\n"
        f"👤 Account Name: "
        f"{get_setting('account_name')}\n"
        f"💳 Account Number: "
        f"{get_setting('account_number')}"
    )


# =========================
# NORMAL MESSAGES
# =========================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "💬 Please choose a service:",
        reply_markup=services_keyboard()
    )


# =========================
# START BOT
# =========================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    init_database()

    app = (
        Application
        .builder()
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
        CommandHandler("stock", change_stock)
    )

    app.add_handler(
        CommandHandler("services", list_services)
    )

    app.add_handler(
        CommandHandler("deleteservice", delete_service)
    )

    app.add_handler(
        CommandHandler("changeaccount", change_account)
    )

    app.add_handler(
        CommandHandler("paymentinfo", payment_info)
    )

    # Buttons
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

    # Normal text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Bensocial Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
