from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
from telegram.error import BadRequest
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8163610288:AAFUT2N6RHsKvQv22xxbFOhWZveJ7cYZUHE"
OWNER_ID = 6663845789  # Replace with your Telegram user ID

# Hardcoded channels for forced subscription
CHANNELS = [
    {"channel_username": "@martline"},
    {"channel_username": "@identicate"},
]

# Mute the user and send the join message
def mute_user(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat

    # Ignore admins, group creators, and the bot owner
    member = context.bot.get_chat_member(chat.id, user.id)
    if member.status in ("administrator", "creator") or user.id == OWNER_ID:
        return

    try:
        # Mute the user using ChatPermissions
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
        )
        context.bot.restrict_chat_member(chat_id=chat.id, user_id=user.id, permissions=permissions)

        # Create join buttons for the channels
        buttons = [
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{channel['channel_username'][1:]}")]
            for channel in CHANNELS
        ]

        buttons.append([InlineKeyboardButton("Verify", callback_data="verify")])
        reply_markup = InlineKeyboardMarkup(buttons)

        # Send the join message
        update.message.reply_text(
            "You need to join the following channels to participate in the group:",
            reply_markup=reply_markup,
        )
    except BadRequest as e:
        logger.error(f"Failed to mute user: {e}")
        update.message.reply_text("The bot needs admin permissions to mute users.")

# Verify the user's membership
def verify_user(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    # Check if the user has joined all channels
    for channel in CHANNELS:
        try:
            member = context.bot.get_chat_member(channel["channel_username"], user.id)
            if member.status not in ("member", "administrator", "creator"):
                query.answer("You haven't joined all required channels.", show_alert=True)
                return
        except BadRequest:
            query.answer("An error occurred while verifying. Please try again later.", show_alert=True)
            return

    # Unmute the user if verification is successful
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        context.bot.restrict_chat_member(chat_id=chat.id, user_id=user.id, permissions=permissions)
        query.answer("Verification successful! You have been unmuted.")
        query.message.reply_text("Thank you for verifying. You can now text in the group!")
    except BadRequest as e:
        logger.error(f"Failed to unmute user: {e}")

# Handle new messages in the group
def handle_message(update: Update, context: CallbackContext):
    mute_user(update, context)

# Global error handler
def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# Main function to set up the bot
def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Callback query handler for "Verify" button
    dispatcher.add_handler(CallbackQueryHandler(verify_user, pattern="^verify$"))

    # Message handler for group messages
    dispatcher.add_handler(MessageHandler(Filters.chat_type.groups, handle_message))

    # Error handler
    dispatcher.add_error_handler(error_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
