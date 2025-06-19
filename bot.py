import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# === CONFIG (Hardcoded) ===
TOKEN = "8048006751:AAHguvRY8bxMq0w8wYwhMc4u7MV3SLXbVMc"  # Your actual bot token
ADMIN_USERNAME = "shirishgoyal30"  # Your Telegram username (without @)

# === LOGGER ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === WHITELIST SET ===
whitelisted_users = set()

# === /start COMMAND ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or user.username or "there"

    if user.username == ADMIN_USERNAME:
        await update.message.reply_text(
            f"👋 Hello {name} (Admin)!\n\n"
            "Welcome to the VCF FN Extractor Bot.\n\n"
            "🛠 Available Admin Commands:\n"
            "➕ /adduser <username> – Add a user\n"
            "➖ /removeuser <username> – Remove a user\n"
            "📋 /listusers – View whitelisted users\n\n"
            "📤 You can also send `.vcf` files to extract FN fields."
        )

    elif user.username in whitelisted_users:
        await update.message.reply_text(
            f"👋 Hello {name}!\n\n"
            "✅ You are whitelisted.\n"
            "📤 Please send or forward a `.vcf` file to extract FN fields."
        )

    else:
        await update.message.reply_text(
            f"👋 Hello {name}!\n\n"
            "🚫 You are not authorized to use this bot.\n"
            "Please contact the admin for access."
        )


# === /adduser ===
async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("🚫 Only the admin can use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /adduser <username>")
        return

    username = context.args[0].replace("@", "")
    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data=f"add:{username}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    await update.message.reply_text(
        f"Do you want to add @{username} to the whitelist?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# === /removeuser ===
async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("🚫 Only the admin can use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /removeuser <username>")
        return

    username = context.args[0].replace("@", "")
    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data=f"remove:{username}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    await update.message.reply_text(
        f"Do you want to remove @{username} from the whitelist?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# === /listusers ===
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("🚫 Only the admin can use this command.")
        return

    if whitelisted_users:
        users = "\n".join(f"@{u}" for u in sorted(whitelisted_users))
        await update.message.reply_text(f"📋 Whitelisted Users:\n{users}")
    else:
        await update.message.reply_text("ℹ️ No users are currently whitelisted.")


# === CALLBACK BUTTON HANDLER ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.username
    await query.answer()

    if user != ADMIN_USERNAME:
        await query.edit_message_text("🚫 Only the admin can use these buttons.")
        return

    data = query.data
    if data.startswith("add:"):
        username = data.split(":", 1)[1]
        whitelisted_users.add(username)
        await query.edit_message_text(f"✅ User @{username} has been added to the whitelist.")

    elif data.startswith("remove:"):
        username = data.split(":", 1)[1]
        if username in whitelisted_users:
            whitelisted_users.remove(username)
            await query.edit_message_text(f"✅ User @{username} has been removed from the whitelist.")
        else:
            await query.edit_message_text(f"⚠️ User @{username} was not in the whitelist.")

    elif data == "cancel":
        await query.edit_message_text("❌ Operation cancelled.")


# === HANDLE .vcf FILE ===
async def handle_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME and user.username not in whitelisted_users:
        await update.message.reply_text("🚫 You are not authorized to use this bot.")
        return

    doc = update.message.document
    if not doc or not doc.file_name.lower().endswith(".vcf"):
        await update.message.reply_text("⚠️ Only `.vcf` files are supported.")
        return

    try:
        file = await context.bot.get_file(doc.file_id)
        file_path = await file.download_to_drive()

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fn_list = [line.strip()[3:] for line in lines if line.startswith("FN:")]

        if fn_list:
            await update.message.reply_text(f"✅ FN Fields Found:\n" + "\n".join(fn_list))
        else:
            await update.message.reply_text("⚠️ No `FN:` fields found in the VCF file.")

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing file:\n{e}")


# === MAIN FUNCTION ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", add_user_command))
    app.add_handler(CommandHandler("removeuser", remove_user_command))
    app.add_handler(CommandHandler("listusers", list_users))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_vcf))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
