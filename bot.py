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

# === WHITELIST STORAGE ===
whitelisted_users = set()

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username in whitelisted_users or user.username == ADMIN_USERNAME:
        await update.message.reply_text("✅ Welcome! Send or forward a .vcf file to extract FN fields.")
    else:
        await update.message.reply_text("❌ You are not authorized to use this bot.")

# === /adduser <username> ===
async def add_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("❌ Only the bot admin can add users.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /adduser <username>")
        return

    new_user = context.args[0].replace("@", "")
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_add:{new_user}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    await update.message.reply_text(
        f"Add @{new_user} to the whitelist?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === /removeuser <username> ===
async def remove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("❌ Only the bot admin can remove users.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /removeuser <username>")
        return

    target_user = context.args[0].replace("@", "")
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_remove:{target_user}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    await update.message.reply_text(
        f"Remove @{target_user} from the whitelist?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# === /listusers ===
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("❌ Only the bot admin can list users.")
        return

    if whitelisted_users:
        users = "\n".join(f"@{u}" for u in sorted(whitelisted_users))
        await update.message.reply_text(f"📋 Whitelisted Users:\n{users}")
    else:
        await update.message.reply_text("ℹ️ No users in the whitelist.")

# === BUTTON HANDLER ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("confirm_add:"):
        username = data.split(":")[1]
        whitelisted_users.add(username)
        await query.edit_message_text(f"✅ User @{username} has been added to the whitelist.")
    elif data.startswith("confirm_remove:"):
        username = data.split(":")[1]
        if username in whitelisted_users:
            whitelisted_users.remove(username)
            await query.edit_message_text(f"✅ User @{username} has been removed from the whitelist.")
        else:
            await query.edit_message_text(f"⚠️ User @{username} is not in the whitelist.")
    elif data == "cancel":
        await query.edit_message_text("❌ Operation cancelled.")

# === HANDLE VCF FILE ===
async def handle_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username not in whitelisted_users and user.username != ADMIN_USERNAME:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    document = update.message.document
    if not document or not document.file_name.lower().endswith(".vcf"):
        await update.message.reply_text("⚠️ Only .vcf files are accepted.")
        return

    try:
        file = await context.bot.get_file(document.file_id)
        file_path = await file.download_to_drive()

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        fn_list = [line.strip()[3:] for line in lines if line.startswith("FN:")]

        if fn_list:
            output = "\n".join(fn_list)
            await update.message.reply_text(f"✅ FN values:\n{output}")
        else:
            await update.message.reply_text("⚠️ No FN fields found.")

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing file:\n{e}")

# === MAIN ===
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
