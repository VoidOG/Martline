from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8163610288:AAFnKCUq5mz5bvGPRDla-3-ay2x-wk9vLaw"

async def kick_phantom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return  # only for groups

    user = update.effective_user
    if not user:
        return

    # Check if "— via @PhantomAdsBot 🚀" in first or last name
    full_name = f"{user.first_name or ''} {user.last_name or ''}".lower()
    if "— via @PhantomAdsBot 🚀" in full_name:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user.id)
            await context.bot.unban_chat_member(update.effective_chat.id, user.id)  # optional (kick instead of ban)
            print(f"Kicked {user.id} ({full_name}) from {update.effective_chat.id}")
        except Exception as e:
            print(f"Failed to kick {user.id}: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, kick_phantom))
    app.run_polling()

if __name__ == "__main__":
    main()
