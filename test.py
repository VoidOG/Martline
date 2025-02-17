import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

# API credentials
api_id = 28561722
api_hash = "a538ba07656f746def99bed7032121cc"
bot_token = "8163610288:AAFnKCUq5mz5bvGPRDla-3-ay2x-wk9vLaw"

app = Client("auto_invite_revoke", api_id, api_hash, bot_token=bot_token)

# Configuration
GROUP_ID = -1002407107904  # Your private group ID
CHANNEL_ID = -1002095589913  # Your channel ID
MESSAGE_LINK = "https://t.me/c/2095589913/5"  # Fixed message link in the repo
OWNER_ID = 6663845789  # Your Telegram ID for logs

current_invite_link = None

async def send_log(text):
    """Send logs to the owner's DM."""
    try:
        await app.send_message(OWNER_ID, text)
    except Exception as e:
        print(f"Error sending log: {e}")

async def update_invite_link():
    global current_invite_link
    while True:
        if current_invite_link:
            try:
                # Revoke all private invite links in the group
                links = await app.get_chat_invite_links(GROUP_ID)
                for link in links:
                    if link.is_revoked is False:
                        await app.revoke_chat_invite_link(GROUP_ID, link.invite_link)
                        await send_log(f"🔴 Revoked invite link: {link.invite_link}")
            except Exception as e:
                await send_log(f"⚠️ Error revoking links: {e}")

        # Create a new invite link (valid for 15 minutes)
        try:
            invite = await app.create_chat_invite_link(GROUP_ID, expire_date=datetime.utcnow() + timedelta(minutes=15))
            current_invite_link = invite.invite_link
            await send_log(f"🟢 New invite link created: {current_invite_link}")
        except Exception as e:
            await send_log(f"⚠️ Error creating invite link: {e}")
            continue  # Skip updating button if link creation fails

        # Update the inline button in your fixed message link
        new_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Group", url=current_invite_link)]])
        try:
            # Extract the message ID from the link and update the inline button
            message_id = MESSAGE_LINK.split("/")[-1]
            await app.edit_message_reply_markup(CHANNEL_ID, message_id, reply_markup=new_markup)
            await send_log(f"✅ Updated inline button in the fixed message: {MESSAGE_LINK}")
        except Exception as e:
            await send_log(f"⚠️ Error updating inline button: {e}")

        await asyncio.sleep(900)  # Wait 15 minutes before regenerating

@app.on_message(filters.new_chat_members)
async def on_new_member(_, message):
    global current_invite_link
    if current_invite_link:
        try:
            await app.revoke_chat_invite_link(GROUP_ID, current_invite_link)
            await send_log(f"⚠️ Invite link revoked after {message.from_user.mention} joined.")
        except Exception as e:
            await send_log(f"⚠️ Error revoking link after user joined: {e}")

async def main():
    await app.start()
    asyncio.create_task(update_invite_link())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
