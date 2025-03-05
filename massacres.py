import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

# API credentials
api_id = 28561722
api_hash = "a538ba07656f746def99bed7032121cc"
bot_token = "8151182853:AAHqUBS6FsI0KJQfDv3_yFWGIwbDYMz33BE"

app = Client("auto_invite_revoke", api_id, api_hash, bot_token=bot_token)

# Configuration
CHANNEL_ID_1 = -1002033219914  # Channel where invite is generated
CHANNEL_ID_2 = -1001761041493  # Channel where button is updated
MESSAGE_ID = 9  # Fixed message ID in CHANNEL_ID_2
ADMIN_IDS = [6663845789, 1110013191]  # List of admin IDs

current_invite_link = None
invite_expiry = 10  # Default expiry time in minutes

async def send_log(text):
    """Send logs to all admins."""
    for admin_id in ADMIN_IDS:
        try:
            await app.send_message(admin_id, f"**[LOG]** {text}", parse_mode="markdown")
        except Exception as e:
            print(f"Error sending log to {admin_id}: {e}")

async def generate_invite_link():
    """Generates a new invite link and updates the button."""
    global current_invite_link

    try:
        # Revoke all existing invite links
        links = await app.get_chat_invite_links(CHANNEL_ID_1)
        for link in links:
            if not link.is_revoked:
                await app.revoke_chat_invite_link(CHANNEL_ID_1, link.invite_link)
                await send_log(f"**[Revoked]** Invite link: `{link.invite_link}`")

        # Create a new invite link with the set expiration time
        invite = await app.create_chat_invite_link(CHANNEL_ID_1, expire_date=datetime.utcnow() + timedelta(minutes=invite_expiry))
        current_invite_link = invite.invite_link
        await send_log(f"**[New Link]** Valid for **{invite_expiry} min**: `{current_invite_link}`")

        # Update the inline button in the fixed message
        new_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=current_invite_link)]])
        await app.edit_message_reply_markup(CHANNEL_ID_2, MESSAGE_ID, reply_markup=new_markup)
        await send_log("**[Updated]** Inline button refreshed.")

    except Exception as e:
        await send_log(f"**[Error]** Updating invite link: `{e}`")

@app.on_message(filters.command("set") & filters.user(ADMIN_IDS))
async def set_expiry_time(_, message):
    """Allows admins to set the invite link expiry time dynamically."""
    global invite_expiry
    try:
        cmd_parts = message.text.split()
        if len(cmd_parts) != 2:
            return await message.reply("**Invalid format.** Use: `/set 10m` or `/set 1h`")

        value = int(cmd_parts[1][:-1])
        unit = cmd_parts[1][-1]

        if unit == "m":
            invite_expiry = value
        elif unit == "h":
            invite_expiry = value * 60
        else:
            return await message.reply("**Invalid unit.** Use 'm' for minutes or 'h' for hours.")

        await message.reply(f"**Invite link expiry set to {invite_expiry} minutes.**")
        await send_log(f"**[Config]** Admin {message.from_user.mention} set expiry to **{invite_expiry} minutes.**")
        await generate_invite_link()  # Generate a new link immediately after changing expiry

    except Exception as e:
        await message.reply("**Error processing your request.**")
        await send_log(f"**[Error]** Setting expiry time: `{e}`")

@app.on_chat_member_updated()
async def on_new_member(_, chat_member):
    """Resets the invite link when a new user joins."""
    if chat_member.new_chat_member:
        await send_log(f"**[User Joined]** {chat_member.new_chat_member.user.mention}")
        await generate_invite_link()  # Generate a new link when someone joins

async def main():
    await app.start()
    await generate_invite_link()  # Generate the first invite link on startup
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
