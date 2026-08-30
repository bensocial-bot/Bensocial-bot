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

# You can keep using your Telegram username.
# For stronger security, you can also add ADMIN_USER_ID in Render.
ADMIN_USERNAME = "silverfoxoftiktok"
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "").strip()

BANK = "Opay (Paycom)"
ACCOUNT_NAME = "Toluwani Awe"
ACCOUNT_NUMBER = "8165405921"

# These are used only to seed the database the first time.
DEFAULT_SERVICES = {
    "whatsapp": {
        "name": "📱 WhatsApp Number",
        "price": "₦4,500",
        "stock": "Available",
        "description": "",
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


def db_connection():
    return sqlite3.connect("users.db")


def init_database():
    conn = db_connection()
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
            service_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price TEXT NOT NULL,
            stock TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT ""
        )
    """)

    # Upgrade an existing database created by the previous bot version.
    cursor.execute("PRAGMA table_info(services)")
    service_columns = {row[1] for row in cursor.fetchall()}
    if "description" not in service_columns:
        cursor.execute(
            'ALTER TABLE services ADD COLUMN description TEXT NOT NULL DEFAULT ""'
        )

    # Add the default services only if they don't already exist.
    for service_id, service in DEFAULT_SERVICES.items():
        cursor.execute("""
            INSERT OR IGNORE INTO services
            (service_id, name, price, stock, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            service_id,
            service["name"],
            service["price"],
            service["stock"],
            service.get("description", ""),
        ))

    conn.commit()
    conn.close()


def get_services():
    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT service_id, name, price, stock, description
        FROM services
        ORDER BY rowid
    """)

    rows = cursor.fetchall()
    conn.close()

    return {
        service_id: {
            "name": name,
            "price": price,
            "stock": stock,
            "description": description or "",
        }
        for service_id, name, price, stock, description in rows
    }


def register_user(user):
    conn = db_connection()
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


def is_admin(user):
    if not user:
        return False

    # Stronger option: if ADMIN_USER_ID is set in Render,
    # use the Telegram numeric ID.
    if ADMIN_USER_ID:
        return str(user.id) == ADMIN_USER_ID

    username = (user.username or "").lstrip("@").lower()
    return username == ADMIN_USERNAME.lstrip("@").lower()


def admin_only(update):
    return is_admin(update.effective_user)


def services_keyboard():
    buttons = []
    services = get_services()
    service_items = list(services.items())

    for i in range(0, len(service_items), 2):
        row = []

        for key, service in service_items[i:i + 2]:
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
            url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    text = (
        "👋 Welcome to Bensocial Bot!\n\n"
        "✅ You have been registered successfully.\n\n"
        "🛍️ Choose a service below to see the price and availability."
    )

    await update.message.reply_text(
        text,
        reply_markup=services_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Bensocial Bot Help\n\n"
        "/start — Open services\n"
        "/help — Show this help\n\n"
        "Choose a service to view its price and stock."
    )

    if is_admin(update.effective_user):
        text += (
            "\n\n🔐 ADMIN COMMANDS\n"
            "/adminhelp — Show admin commands\n"
            "/services — List all services\n"
            "/addservice — Add a service\n"
            "/changeprice — Change a price\n"
            "/stock — Change stock\n"
            "/changedescription — Change service description\n"
            "/deleteservice — Delete a service"
        )

    await update.message.reply_text(text)


async def adminhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("❌ Admin access only.")
        return

    await update.message.reply_text(
        "🔐 ADMIN PANEL\n\n"
        "➕ Add service:\n"
        "/addservice key | name | price | stock\n\n"
        "Example:\n"
        "/addservice web_design | 🌐 Website Design | ₦30,000 | 10\n\n"
        "💰 Change price:\n"
        "/changeprice key | new price\n\n"
        "📝 Change description:\n"
        "/changedescription key | new description\n\n"
        "Example:\n"
        "/changeprice whatsapp | ₦5,000\n\n"
        "📦 Change stock:\n"
        "/stock key | new stock\n\n"
        "Example:\n"
        "/stock whatsapp | 20\n\n"
        "📋 List services:\n"
        "/services\n\n"
        "🗑️ Delete service:\n"
        "/deleteservice key\n\n"
        "💡 The key should be simple: letters, numbers and underscores."
    )


async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("❌ Admin access only.")
        return

    services = get_services()

    if not services:
        await update.message.reply_text("📭 No services found.")
        return

    lines = ["📋 CURRENT SERVICES\n"]

    for key, service in services.items():
        lines.append(
            f"• {key}\n"
            f"  {service['name']}\n"
            f"  💰 {service['price']} | 📦 Stock: {service['stock']}\n"
            + (f"  📝 {service['description']}\n" if service.get("description") else "")
        )

    await update.message.reply_text("\n".join(lines))


async def addservice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("❌ Admin access only.")
        return

    raw = update.message.text.partition(" ")[2].strip()

    if not raw:
        await update.message.reply_text(
            "❌ Format:\n"
            "/addservice key | name | price | stock\n\n"
            "Example:\n"
            "/addservice web_design | 🌐 Website Design | ₦30,000 | 10"
        )
        return

    parts = [part.strip() for part in raw.split("|")]

    if len(parts) != 4:
        await update.message.reply_text(
            "❌ You need exactly 4 parts:\n"
            "key | name | price | stock"
        )
        return

    service_id, name, price, stock = parts

    if not service_id or not name or not price or not stock:
        await update.message.reply_text("❌ None of the fields can be empty.")
        return

    if any(char in service_id for char in " |/\\"):
        await update.message.reply_text(
            "❌ Invalid key. Use only letters, numbers and underscores."
        )
        return

    conn = db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO services
            (service_id, name, price, stock, description)
            VALUES (?, ?, ?, ?, ?)
        """, (service_id, name, price, stock, description))

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        await update.message.reply_text(
            f"❌ Service key '{service_id}' already exists.\n"
            "Use /changeprice or /stock, or choose another key."
        )
        return

    conn.close()

    await update.message.reply_text(
        "✅ Service added successfully!\n\n"
        f"🔑 Key: {service_id}\n"
        f"🛍️ Name: {name}\n"
        f"💰 Price: {price}\n"
        f"📦 Stock: {stock}\n"
        f"📝 Description: {description or '(none)'}"
    )


async def changedescription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("❌ Admin access only.")
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [part.strip() for part in raw.split("|", 1)]

    if len(parts) != 2 or not parts[0] or not parts[1]:
        await update.message.reply_text(
            "❌ Format:\n"
            "/changedescription key | new description\n\n"
            "Example:\n"
            "/changedescription tiktok_followers | ⚡ Speed: 100K/day; 🔄 Refill: 30 days; ⚡ Instant start"
        )
        return

    service_id, new_description = parts

    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE services SET description = ? WHERE service_id = ?",
        (new_description, service_id)
    )
    changed = cursor.rowcount
    conn.commit()
    conn.close()

    if changed == 0:
        await update.message.reply_text(
            f"❌ Service '{service_id}' was not found."
        )
        return

    await update.message.reply_text(
        f"✅ Description updated!\n\n"
        f"🛍️ Service: {service_id}\n"
        f"📝 New description: {new_description}"
    )


async def changeprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("❌ Admin access only.")
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [part.strip() for part in raw.split("|")]

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Format:\n"
            "/changeprice key | new price\n\n"
            "Example:\n"
            "/changeprice whatsapp | ₦5,000"
        )
        return

    service_id, new_price = parts

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET price = ?
        WHERE service_id = ?
    """, (new_price, service_id))

    changed = cursor.rowcount
    conn.commit()
    conn.close()

    if changed == 0:
        await update.message.reply_text(
            f"❌ Service '{service_id}' was not found."
        )
        return

    await update.message.reply_text(
        f"✅ Price updated!\n\n"
        f"🛍️ Service: {service_id}\n"
        f"💰 New price: {new_price}"
    )


async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("❌ Admin access only.")
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [part.strip() for part in raw.split("|")]

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Format:\n"
            "/stock key | new stock\n\n"
            "Examples:\n"
            "/stock whatsapp | 20\n"
            "/stock whatsapp | Out of stock\n"
            "/stock whatsapp | Available"
        )
        return

    service_id, new_stock = parts

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE services
        SET stock = ?
        WHERE service_id = ?
    """, (new_stock, service_id))

    changed = cursor.rowcount
    conn.commit()
    conn.close()

    if changed == 0:
        await update.message.reply_text(
            f"❌ Service '{service_id}' was not found."
        )
        return

    await update.message.reply_text(
        f"✅ Stock updated!\n\n"
        f"🛍️ Service: {service_id}\n"
        f"📦 New stock: {new_stock}"
    )


async def deleteservice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        await update.message.reply_text("❌ Admin access only.")
        return

    raw = update.message.text.partition(" ")[2].strip()

    if not raw:
        await update.message.reply_text(
            "❌ Format:\n"
            "/deleteservice key\n\n"
            "Example:\n"
            "/deleteservice web_design"
        )
        return

    service_id = raw.split()[0]

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM services WHERE service_id = ?",
        (service_id,)
    )

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        await update.message.reply_text(
            f"❌ Service '{service_id}' was not found."
        )
        return

    await update.message.reply_text(
        f"🗑️ Service '{service_id}' deleted successfully."
    )


async def service_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    key = query.data.replace("service:", "")
    services = get_services()
    service = services.get(key)

    if not service:
        await query.edit_message_text(
            "❌ Service not found or has been removed.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ Back to Services",
                        callback_data="back_services"
                    )
                ]
            ])
        )
        return

    description = service.get("description", "").strip()

    text = (
        f"{service['name']}\n\n"
        + (f"{description}\n\n" if description else "")
        + f"💰 Price: {service['price']}\n"
        f"📦 Stock: {service['stock']}\n\n"
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
                url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"
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


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    register_user(update.effective_user)

    await update.message.reply_text(
        "💬 Please choose a service from the menu below.",
        reply_markup=services_keyboard()
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    init_database()

    app = Application.builder().token(BOT_TOKEN).build()

    # Customer commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Admin commands
    app.add_handler(CommandHandler("adminhelp", adminhelp))
    app.add_handler(CommandHandler("services", services_command))
    app.add_handler(CommandHandler("addservice", addservice))
    app.add_handler(CommandHandler("changeprice", changeprice))
    app.add_handler(CommandHandler("changedescription", changedescription))
    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("deleteservice", deleteservice))

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
