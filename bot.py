from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# === CONFIG (Hardcoded) ===
TOKEN = "8048006751:AAHguvRY8bxMq0w8wYwhMc4u7MV3SLXbVMc"  # Your actual bot token
ADMIN_USERNAME = "shirishgoyal30"  # Your Telegram username (without @)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        await update.message.reply_text("❌ You are not admin.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Add", callback_data="add:testuser")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])

    await update.message.reply_text(
        "Add @testuser to whitelist?",
        reply_markup=keyboard
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("add:"):
        username = query.data.split(":")[1]
        await query.edit_message_text(f"✅ Added @{username}")
    elif query.data == "cancel":
        await query.edit_message_text("❌ Cancelled")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
