from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from telegram.error import BadRequest

# Configuration
BOT_TOKEN = "8163610288:AAFUT2N6RHsKvQv22xxbFOhWZveJ7cYZUHE"
OWNER_ID = 6663845789
MONGO_URI = "mongodb+srv://Cenzo:Cenzo123@cenzo.azbk1.mongodb.net"
REQUIRED_CHANNELS = ["martline", "identicate"]

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["bot_database"]
verified_users = db["verified_users"]

# Function to save verified user
def save_verified_user(user_id):
    if not verified_users.find_one({"user_id": user_id}):
        verified_users.insert_one({"user_id": user_id})

# Function to check if user is verified
def is_user_verified(user_id):
    return verified_users.find_one({"user_id": user_id}) is not None

# Function to remove user from verified list (if they leave fsub channels)
def remove_verified_user(user_id):
    verified_users.delete_one({"user_id": user_id})

# Function to check if user has joined all required channels
def has_joined_required_channels(bot, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(f"@{channel}", user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except BadRequest:
            return False
    return True

# Function to handle new messages and mute unverified users
def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat

    # Ignore admins, group creators, and the bot owner
    member = context.bot.get_chat_member(chat.id, user.id)
    if member.status in ("administrator", "creator") or user.id == OWNER_ID:
        return

    # Check if user has left the channels
    if not has_joined_required_channels(context.bot, user.id):
        remove_verified_user(user.id)  # Remove from verified list
        # Mute the user
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
        )
        context.bot.restrict_chat_member(chat_id=chat.id, user_id=user.id, permissions=permissions)

        # Send verification message
        buttons = [
            [InlineKeyboardButton("𝖩𝗈𝗂𝗇 𝖢𝗁𝖺𝗇𝗇𝖾𝗅", url="https://t.me/martline")],
            [InlineKeyboardButton("𝖩𝗈𝗂𝗇 𝖢𝗁𝖺𝗇𝗇𝖾𝗅", url="https://t.me/identicate")],
            [InlineKeyboardButton("𝖵𝖾𝗋𝗂𝖿𝗒", callback_data="verify")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        update.message.reply_text(
            "𝖸𝗈𝗎 𝗇𝖾𝖾𝖽 𝗍𝗈 𝗃𝗈𝗂𝗇 𝗍𝗁𝖾 𝖿𝗈𝗅𝗅𝗈𝗐𝗂𝗇𝗀 𝖼𝗁𝖺𝗇𝗇𝖾𝗅𝗌 𝗍𝗈 𝗍𝖾𝗑𝗍 𝗂𝗇 𝗍𝗁𝖾 𝗀𝗋𝗈𝗎𝗉:",
            reply_markup=reply_markup,
        )
    else:
        # If user is verified, allow them to send messages
        if not is_user_verified(user.id):
            save_verified_user(user.id)

# Function to handle verification
def verify_user(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    # Check if the user has joined all channels
    if has_joined_required_channels(context.bot, user.id):
        save_verified_user(user.id)

        # Unmute the user
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        context.bot.restrict_chat_member(chat_id=chat.id, user_id=user.id, permissions=permissions)

        query.answer("𝖵𝖾𝗋𝗂𝖿𝗂𝖼𝖺𝗍𝗂𝗈𝗇 𝗌𝗎𝖼𝖼𝖾𝗌𝗌𝖿𝗎𝗅 ✅! 𝖸𝗈𝗎 𝗁𝖺𝗏𝖾 𝖻𝖾𝖾𝗇 𝗎𝗇𝗆𝗎𝗍𝖾𝖽.")
        query.message.reply_text("𝖳𝗁𝖺𝗇𝗄 𝗒𝗈𝗎 𝖿𝗈𝗋 𝗏𝖾𝗋𝗂𝖿𝗒𝗂𝗇𝗀. 𝖸𝗈𝗎 𝖼𝖺𝗇 𝗇𝗈𝗐 𝗍𝖾𝗑𝗍 𝗂𝗇 𝗍𝗁𝖾 𝗀𝗋𝗈𝗎𝗉!")
    else:
        query.answer("𝖸𝗈𝗎 𝗁𝖺𝗏𝖾𝗇'𝗍 𝗃𝗈𝗂𝗇𝖾𝖽 𝖺𝗅𝗅 𝗋𝖾𝗊𝗎𝗂𝗋𝖾𝖽 𝖼𝗁𝖺𝗇𝗇𝖾𝗅𝗌.", show_alert=True)

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("𝗪𝗲𝗹𝗰𝗼𝗺𝗲!\n𝖨 𝖾𝗇𝗌𝗎𝗋𝖾 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝗃𝗈𝗂𝗇𝖾𝖽 𝗍𝗁𝖾 𝗋𝖾𝗊𝗎𝗂𝗋𝖾𝖽 𝖼𝗁𝖺𝗇𝗇𝖾𝗅𝗌 𝗍𝗈 𝗍𝖾𝗑𝗍 𝗂𝗇 𝖬𝖺𝗋𝗍𝗅𝗂𝗇𝖾 𝖬𝖺𝗋𝗄𝖾𝗍𝗉𝗅𝖺𝖼𝖾. \n@Martline")

# Main function to start the bot
def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(verify_user, pattern="verify"))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
