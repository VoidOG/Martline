import time
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from telegram.error import BadRequest

# Configuration
BOT_TOKEN = "8163610288:AAF_on08IJBRF9tZCnZOZS7T8PCH22voz5w"
OWNER_ID = 6663845789
MONGO_URI = "mongodb+srv://Cenzo:Cenzo123@cenzo.azbk1.mongodb.net"
REQUIRED_CHANNEL = "martline"      # only one channel

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["sex"]
verified_users = db["sex"]

# Uptime
START_TIME = time.time()

# Helper functions
def get_uptime():
    seconds = int(time.time() - START_TIME)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return f"{d}d {h}h {m}m {s}s"

def save_verified_user(user_id):
    if not verified_users.find_one({"user_id": user_id}):
        verified_users.insert_one({"user_id": user_id, "muted": False})

def is_user_verified(user_id):
    doc = verified_users.find_one({"user_id": user_id})
    return doc is not None and not doc.get("muted", False)

def set_user_muted(user_id, muted=True):
    verified_users.update_one({"user_id": user_id}, {"$set": {"muted": muted}}, upsert=True)

def remove_user(user_id):
    verified_users.delete_one({"user_id": user_id})

def has_joined_required_channel(bot, user_id):
    try:
        member = bot.get_chat_member(f"@{REQUIRED_CHANNEL}", user_id)
        if member.status in ("member", "administrator", "creator"):
            return True
    except BadRequest:
        pass
    return False

def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    chat = update.effective_chat

    # Ignore admins, creator & owner 
    member = context.bot.get_chat_member(chat.id, user.id)
    if member.status in ("administrator", "creator") or user.id == OWNER_ID:
        return

    # Only fsub in one group
   # if chat.id != -1002042217396:   # apne group ka ID daaliye, ya comment kare to sab jagah chalega
        return

    # Forced subscription logic
    if not has_joined_required_channel(context.bot, user.id):
        set_user_muted(user.id, muted=True)
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
        )
        context.bot.restrict_chat_member(chat.id, user.id, permissions=permissions)

        buttons = [
            [InlineKeyboardButton("Channel join karo", url=f"https://t.me/{REQUIRED_CHANNEL}")],
            [InlineKeyboardButton("Verify karo", callback_data="verify")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(
            "Bhai group me likhne ke liye neeche waala channel join karo, fir 'Verify karo' dabao.",
            reply_markup=reply_markup,
        )
    else:
        if not is_user_verified(user.id):
            save_verified_user(user.id)
            set_user_muted(user.id, muted=False)

def verify_user(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat

    if not has_joined_required_channel(context.bot, user.id):
        query.answer("Aapne abhi tak required channel join nahi kiya hai!", show_alert=True)
        return

    save_verified_user(user.id)
    set_user_muted(user.id, muted=False)

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_invite_users=True,
    )
    context.bot.restrict_chat_member(chat.id, user.id, permissions=permissions)
    query.answer("Verify ho gaye ho! Ab group me likh sakte ho ✅")

    query.message.reply_text("Shukriya! Ab aap group me message kar sakte ho.")

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id == OWNER_ID:
        total_users = verified_users.count_documents({})
        verified_count = verified_users.count_documents({"muted": False})
        muted_count = verified_users.count_documents({"muted": True})
        uptime = get_uptime()
        update.message.reply_text(
            f"Bot Uptime: {uptime}\n"
            f"Verified Users: {verified_count}\n"
            f"Muted Users: {muted_count}\n"
            f"Total Users: {total_users}"
        )
    else:
        buttons = [
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL}")],
            [InlineKeyboardButton("Verify", callback_data="verify")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(
            "Welcome! To chat in this group, kindly join the required channel below, then tap 'Verify'.",
            reply_markup=reply_markup,
        )

def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(verify_user, pattern="verify"))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
  
