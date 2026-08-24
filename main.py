import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Configuration
API_ID = 33772941
API_HASH = "3b6ab6b1940c87915439bb41e4e80ea8"
BOT_TOKEN = "8580109392:AAH_IASAWo3vAiPAfSNbr_l_Yk8UG72V6R0"

ADMIN_ID = 6132146801  # Main Admin Telegram User ID
MANDATORY_CHANNELS = ["nobitabanxunban", "O1CtosbUTxU2ODBl"]  # Username or Invite Link Slug

app = Client("usdt_giveaway_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# In-Memory Databases (Production me Database use karein)
users_db = set()
premium_users = set()

# Helper Function: Check Mandatory Join
async def check_joined(user_id: int, client: Client) -> bool:
    for ch in MANDATORY_CHANNELS:
        try:
            chat_id = ch if ch.startswith("-100") else f"@{ch.replace('https://t.me/+', '')}"
            member = await client.get_chat_member(chat_id, user_id)
            if member.status in ["kicked", "left"]:
                return False
        except Exception:
            # Private link handling fallback
            pass
    return True

# Channel Join Keyboard
join_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/nobitabanxunban")],
    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/+O1CtosbUTxU2ODBl")],
    [InlineKeyboardButton("🔄 Verify / Start", callback_data="verify_join")]
])

# Main Menu Keyboard
def get_main_menu(user_id):
    buttons = [
        [InlineKeyboardButton("🎁 Claim USDT Giveaway", callback_data="claim_giveaway")],
        [InlineKeyboardButton("💎 Purchase Premium ($50)", callback_data="buy_premium")],
        [InlineKeyboardButton("👨‍💻 Contact Owner", url="https://t.me/Znonsence")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

# Command: /start
@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    users_db.add(user_id)

    is_joined = await check_joined(user_id, client)
    if not is_joined:
        await message.reply_text(
            "✨ **Welcome to USDT Giveaway Bot!** ✨\n\n"
            "⚠️ *Bot use karne ke liye pehele dono channels join karna mandatory hai:*",
            reply_markup=join_keyboard
        )
        return

    premium_status = "🌟 Premium User" if user_id in premium_users or user_id == ADMIN_ID else "🆓 Free User"
    
    text = (
        "💎 <b>WELCOME TO VIP USDT GIVEAWAY BOT</b> 💎\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {message.from_user.mention}\n"
        f"🛡️ <b>Status:</b> {premium_status}\n\n"
        "⚡ <i>Fast, Secure & Automated USDT Rewards!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Neeche diye gaye buttons se navigate karein:"
    )
    await message.reply_text(text, reply_markup=get_main_menu(user_id))

# Callback Query Handler
@app.on_callback_query()
async def callback_handler(client: Client, query):
    user_id = query.from_user.id
    data = query.data

    if data == "verify_join":
        is_joined = await check_joined(user_id, client)
        if is_joined:
            await query.message.edit_text("✅ *Verification Successful!*", reply_markup=get_main_menu(user_id))
        else:
            await query.answer("❌ Aapne dono channels join nahi kiye hain!", show_alert=True)

    elif data == "claim_giveaway":
        if user_id not in premium_users and user_id != ADMIN_ID:
            await query.answer("🔒 Yeh giveaway strictly Premium users ke liye hai!", show_alert=True)
            return
        await query.message.edit_text("🎉 **USDT Giveaway Claimed Successfully!**\n\nBalance aapke account me 24h me credit ho jayega.")

    elif data == "buy_premium":
        text = (
            "💎 **VIP PREMIUM MEMBERSHIP** 💎\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 **Price:** `$50 USDT` (Lifetime Access)\n\n"
            "🔥 **Benefits:**\n"
            "• Direct USDT Giveaway Access\n"
            "• Fast Payout Processing\n"
            "• 24/7 VIP Support\n\n"
            "💳 Purchase karne ke liye Owner ko contact karein."
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📩 Contact Owner", url="https://t.me/Znonsence")]])
        await query.message.edit_text(text, reply_markup=kb)

    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            return
        text = (
            "⚙️ **ADMIN CONTROL PANEL** ⚙️\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• `/broadcast <message>` - Sabhi users ko message bhejne ke liye\n"
            "• `/addpremium <user_id>` - User ko Premium dene ke liye\n"
            "• `/stats` - Total Bot Users check karne ke liye"
        )
        await query.message.edit_text(text)

# Admin Command: /stats
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_cmd(client: Client, message: Message):
    total = len(users_db)
    premium_cnt = len(premium_users)
    await message.reply_text(
        "📊 **BOT STATISTICS** 📊\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **Total Users:** `{total}`\n"
        f"💎 **Premium Users:** `{premium_cnt}`"
    )

# Admin Command: /addpremium
@app.on_message(filters.command("addpremium") & filters.user(ADMIN_ID))
async def add_premium_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/addpremium <user_id>`")
        return
    try:
        target_id = int(message.command[1])
        premium_users.add(target_id)
        await message.reply_text(f"✅ User `{target_id}` ko Premium Access de diya gaya hai.")
    except ValueError:
        await message.reply_text("❌ Invalid User ID!")

# Admin Command: /broadcast
@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID))
async def broadcast_cmd(client: Client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply_text("📢 Usage: Message ke reply me `/broadcast` likhein ya text `/broadcast Hello` aise bhein.")
        return

    msg_to_send = message.reply_to_message if message.reply_to_message else message.text.split(None, 1)[1]
    
    sent = 0
    failed = 0
    status_msg = await message.reply_text("🚀 Broadcasting started...")

    for uid in list(users_db):
        try:
            if message.reply_to_message:
                await msg_to_send.copy(uid)
            else:
                await client.send_message(uid, msg_to_send)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        "📢 **BROADCAST COMPLETED** 📢\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ **Success:** `{sent}`\n"
        f"❌ **Failed:** `{failed}`"
    )

if __name__ == "__main__":
    app.run()
