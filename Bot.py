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

ADMIN_USERNAME = "silverfoxoftiktok"

BANK = "Opay (Paycom)"
ACCOUNT_NAME = "Toluwani Awe"
ACCOUNT_NUMBER = "8165405921"


SERVICES = {
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


def init_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
    """)

    conn.commit()
    conn.close()


def register_user(user):
    conn = sqlite3.connect("users.db")
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


def services_keyboard():
    buttons = []

    service_items = list(SERVICES.items())

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
            url=f"https://t.me/{ADMIN_USERNAME}"
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
    await update.message.reply_text(
        "🤖 Bensocial Bot Help\n\n"
        "/start — Open services\n"
        "/help — Show this help\n\n"
        "Choose a service to view its price and stock."
    )


async def service_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    key = query.data.replace("service:", "")

    service = SERVICES.get(key)

    if not service:
        await query.edit_message_text(
            "❌ Service not found."
        )
        return

    text = (
        f"{service['name']}\n\n"
        f"💰 Price: {service['price']}\n"
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

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
