import logging
import unicodedata
from telegram import Update, User
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# IMPORTANT: use env var in prod
BOT_TOKEN = "7667383525:AAEIhwn2IhwbAsqM79yywr0b-TIw9V9FfYY"

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).lower().strip()
    replacements = {
        "—": "-",   # em dash -> hyphen
        "–": "-",   # en dash -> hyphen
        "🚀": "",   # drop emoji
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    s = " ".join(s.split())
    return s

SPAM_PATTERNS = [
    "— via @phantomadsbot 🚀",
    "— via @phantomadsbot",
    "via @phantomadsbot",
    "@phantomadsbot",
    "phantomadsbot",
    "- via @phantomadsbot",
    "adbot - via @camprunBot 🚀",
    "adbot"
    # ASCII-safe fallback
]

def matches_spam_profile(user: User) -> bool:
    first = normalize_text(user.first_name or "")
    last = normalize_text(user.last_name or "")
    uname = normalize_text(user.username or "")
    full_name = f"{first} {last}".strip()
    for pat in SPAM_PATTERNS:
        np = normalize_text(pat)
        if np in full_name or (uname and np in uname):
            return True
    return False

async def kick_user_safely(user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE, reason: str) -> bool:
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            logger.error("Bot is not admin. Grant admin + 'Ban users'.")
            return False
        if not getattr(bot_member, "can_restrict_members", False):
            logger.error("Bot lacks 'Ban users' permission.")
            return False

        # Kick: ban + unban
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id)
        logger.info(f"Kicked user {user_id}. Reason: {reason}")
        return True

    except TelegramError as e:
        logger.error(f"Telegram error kicking user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error kicking user {user_id}: {e}")
        return False

async def on_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat or chat.type not in ["group", "supergroup"]:
        return
    msg = update.message
    if not msg or not msg.text:
        return
    user = update.effective_user
    if not user:
        return

    # Only name/username based filter, triggered by message
    if matches_spam_profile(user):
        await kick_user_safely(user.id, chat.id, context, "Profile signature detected")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Only handle new text messages; no join handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_new_message))

    logger.info("Anti-Phantom (message-only, name filter) starting...")
    logger.info("Make the bot admin with 'Ban users'. Consider disabling BotFather group privacy.")

    app.run_polling(allowed_updates=["message"], drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
