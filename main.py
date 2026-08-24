import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
)

# ---------------------------------------------------------
# BOT CONFIGURATION
# ---------------------------------------------------------
BOT_TOKEN = "8999949252:AAFajrj8WNlHWU9Px13VpltL2j1cPzyiPxY"
BOT_USERNAME = "@Usdt_giveway_bot"

# Admin IDs (Apna Telegram Numeric User ID yahan daalein)
ADMIN_IDS = [123456789]  # Replace with your actual Telegram User ID

# Channels Config
MANDATORY_CHANNEL = "@nobitabanxunban"
MANDATORY_CHANNEL_LINK = "https://t.me/nobitabanxunban"
PRIVATE_CHANNEL_LINK = "https://t.me/+ckvWhC-ac90zZTk1"

# Banner Images
GIVEAWAY_PHOTO = "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=1000"

# Economic Settings
MIN_WITHDRAW = 5.0      # USDT Threshold
DAILY_BONUS = 0.05      # USDT
REFERRAL_BONUS = 0.50   # USDT

# ---------------------------------------------------------
# DATABASE & LOGS
# ---------------------------------------------------------
users_db = {}
withdrawal_requests = []

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def is_user_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=MANDATORY_CHANNEL, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
    except Exception as e:
        logging.warning(f"Membership check failed: {e}")
        return False
    return False

def init_user(user_id, username=None):
    if user_id not in users_db:
        users_db[user_id] = {
            "balance": 0.0,
            "referrals": 0,
            "claimed_today": False,
            "wallet": None,
            "username": username or "User",
            "joined": False
        }

# ---------------------------------------------------------
# START & VERIFICATION
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name
    init_user(user_id, user.username)

    if context.args and not users_db[user_id]["joined"]:
        try:
            referrer_id = int(context.args[0])
            if referrer_id in users_db and referrer_id != user_id:
                users_db[user_id]["referred_by"] = referrer_id
        except ValueError:
            pass

    keyboard = [
        [InlineKeyboardButton("📢 1️⃣ Join Main Channel (Mandatory)", url=MANDATORY_CHANNEL_LINK)],
        [InlineKeyboardButton("🔒 2️⃣ Request VIP Channel Access", url=PRIVATE_CHANNEL_LINK)],
        [InlineKeyboardButton("⚡ 3️⃣ VERIFY & CLAIM REWARDS ⚡", callback_data="verify_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"👑 *⚡ 𝗛𝗘𝗬𝗬 {first_name.upper()} ⚡*\n\n"
        f"🔥 *𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗨𝗦𝗗𝗧 𝗚𝗜𝗩𝗘𝗔𝗪𝗔𝗬 𝗕𝗢𝗧* 🔥\n\n"
        f"🏆 *💎 Premium USDT Rewards System 💎*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 *Daily Bonus:* `{DAILY_BONUS:.2f} USDT` / 24 Hours\n"
        f"👥 *Per Referral:* `{REFERRAL_BONUS:.2f} USDT` (Instant)\n"
        f"💸 *Min. Payout:* `{MIN_WITHDRAW:.2f} USDT` (BEP20 / TRC20)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👇 *Niche diye gaye 2 Channels join karein aur Verify button par click karein!*"
    )

    await update.message.reply_photo(
        photo=GIVEAWAY_PHOTO,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    init_user(user_id, query.from_user.username)

    joined = await is_user_joined(user_id, context)
    
    if joined:
        if not users_db[user_id]["joined"] and "referred_by" in users_db[user_id]:
            ref_id = users_db[user_id]["referred_by"]
            if ref_id in users_db:
                users_db[ref_id]["balance"] += REFERRAL_BONUS
                users_db[ref_id]["referrals"] += 1
                try:
                    await context.bot.send_message(
                        chat_id=ref_id,
                        text=(
                            f"🎉 *New Referral Joined!*\n\n"
                            f"👤 User: `{query.from_user.first_name}`\n"
                            f"➕ Added: `+{REFERRAL_BONUS:.2f} USDT` 💎"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

        users_db[user_id]["joined"] = True
        await query.answer("✅ Verification Successful! Welcome!", show_alert=True)
        await show_main_menu(query.message, query.from_user.first_name)
    else:
        await query.answer("❌ Verification Failed! Pehle Main Channel join karein.", show_alert=True)

async def show_main_menu(message, name):
    menu_keyboard = [
        [KeyboardButton("💰 Balance"), KeyboardButton("🎁 Daily Bonus")],
        [KeyboardButton("🔗 Referral Link"), KeyboardButton("💸 Premium Withdraw")],
        [KeyboardButton("📊 Leaderboard"), KeyboardButton("⚙️ Set Wallet"), KeyboardButton("📞 Support")]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)

    text = (
        f"🌟 *WELCOME TO DASHBOARD, {name.upper()}!* 🌟\n\n"
        f"✅ Aapka account verified hai.\n"
        f"🚀 Niche Menu se Option select karein aur USDT earn karna shuru karein!"
    )
    await message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# ---------------------------------------------------------
# MAIN KEYBOARD MENU HANDLERS
# ---------------------------------------------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    init_user(user_id, update.effective_user.username)

    if not users_db[user_id]["joined"]:
        await update.message.reply_text("⚠️ Pehle `/start` dabakar channels verify karein!", parse_mode="Markdown")
        return

    if text == "💰 Balance":
        bal = users_db[user_id]["balance"]
        refs = users_db[user_id]["referrals"]
        wallet = users_db[user_id]["wallet"] or "Not Set (⚙️ Set Wallet par click karein)"
        
        reply = (
            f"💳 *⚡ 𝗬𝗢𝗨𝗥 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 ⚡*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* `{update.effective_user.first_name}`\n"
            f"💵 *USDT Balance:* `{bal:.4f} USDT` 💎\n"
            f"👥 *Total Referrals:* `{refs} Users` 🔥\n"
            f"👛 *Configured Wallet:* `{wallet}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Next Goal:* Minimum `{MIN_WITHDRAW:.2f} USDT` to Payout!"
        )
        await update.message.reply_text(reply, parse_mode="Markdown")

    elif text == "🎁 Daily Bonus":
        if not users_db[user_id]["claimed_today"]:
            users_db[user_id]["balance"] += DAILY_BONUS
            users_db[user_id]["claimed_today"] = True
            await update.message.reply_text(
                f"🎉 *DAILY REWARD CLAIMED!* 🎉\n\n"
                f"✅ Aapke account me *+{DAILY_BONUS:.2f} USDT* add kar diye gaye hain!\n"
                f"⏰ Agla bonus 24 ghante baad milega.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "⏳ *Bonus Already Claimed!*\n\nAapne aaj ka bonus claim kar liya hai. Kal wapas aana! 🕒",
                parse_mode="Markdown"
            )

    elif text == "🔗 Referral Link":
        ref_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}"
        refs = users_db[user_id]["referrals"]
        
        caption = (
            f"🚀 *⚡ 𝗥𝗘𝗙𝗘𝗥 𝗔𝗡𝗗 𝗘𝗔𝗥𝗡 𝗨𝗦𝗗𝗧 ⚡*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 *Reward Per Refer:* `{REFERRAL_BONUS:.2f} USDT` 💎\n"
            f"👥 *Your Total Referrals:* `{refs}`\n\n"
            f"🔗 *Your Exclusive Invite Link:*\n"
            f"`{ref_link}`\n\n"
            f"📌 *Rules:* Friends ko share karein. Verify karne par instant `{REFERRAL_BONUS:.2f} USDT` milega!"
        )
        keyboard = [[InlineKeyboardButton("📢 Share With Friends", url=f"https://t.me/share/url?url={ref_link}&text=Join%20USDT%20Giveaway%20Bot%20and%20Earn%20Free%20USDT!")]]
        await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "⚙️ Set Wallet":
        await update.message.reply_text(
            "⚙️ *SET / UPDATE USDT ADDRESS*\n\n"
            "Apna **USDT (TRC-20 / BEP-20)** Wallet Address send karein:\n"
            "Example command: `/setwallet T9yD14Nj9j7xGzV16t5H2bV1...`",
            parse_mode="Markdown"
        )

    elif text == "💸 Premium Withdraw":
        bal = users_db[user_id]["balance"]
        wallet = users_db[user_id]["wallet"]
        
        if not wallet:
            await update.message.reply_text(
                "⚠️ *WALLET NOT SET!*\n\n"
                "Pehle apna USDT Wallet set karein.\n"
                "Command: `/setwallet YOUR_WALLET_ADDRESS`",
                parse_mode="Markdown"
            )
            return

        if bal < MIN_WITHDRAW:
            needed = MIN_WITHDRAW - bal
            refs_needed = int((needed // REFERRAL_BONUS) + (1 if needed % REFERRAL_BONUS != 0 else 0))
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Invite Friends Now", callback_data="get_ref")]
            ])
            
            await update.message.reply_text(
                f"❌ *WITHDRAWAL LOCK DETECTED!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💳 *Current Balance:* `{bal:.4f} USDT`\n"
                f"🎯 *Minimum Payout:* `{MIN_WITHDRAW:.2f} USDT`\n"
                f"🔻 *Shortage:* `{needed:.4f} USDT`\n\n"
                f"💡 *Kaise Unlock Karein?*\n"
                f"Aapko bas *{refs_needed} aur refer* karne hain payout threshold unlock karne ke liye! 🚀",
                parse_mode="Markdown",
                reply_markup=kb
            )
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚡ Confirm & Instant Payout", callback_data="confirm_withdraw")],
                [InlineKeyboardButton("❌ Cancel Request", callback_data="cancel_withdraw")]
            ])
            
            await update.message.reply_text(
                f"👑 *⚡ 𝗨𝗦𝗗𝗧 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 ⚡*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 *User:* `{update.effective_user.first_name}`\n"
                f"💵 *Requested Amount:* `{bal:.4f} USDT`\n"
                f"👛 *Destination Wallet:* `{wallet}`\n"
                f"⚡ *Network:* USDT (TRC-20 / BEP-20)\n"
                f"🛡️ *Fee:* `0.00 USDT` (FREE)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Confirmation:* Kya aap instant withdrawal trigger karna chahte hain?",
                parse_mode="Markdown",
                reply_markup=kb
            )

    elif text == "📊 Leaderboard":
        await update.message.reply_text(
            "🏆 *⚡ 𝗧𝗢𝗣 𝗥𝗘𝗙𝗘𝗥𝗥𝗘𝗥𝗦 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗 ⚡*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🥇 1. @CryptoKing_99 — `145.50 USDT` 🔥\n"
            "🥈 2. @Alex_Trader — `92.00 USDT` 💎\n"
            "🥉 3. @Rahul_Pro — `68.50 USDT` ✨\n"
            "4️⃣ 4. @Sami_Earn — `44.00 USDT` 🚀\n"
            "5️⃣ 5. @Vip_User12 — `31.50 USDT` ⚡\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎁 *Top users get monthly extra rewards!*",
            parse_mode="Markdown"
        )

    elif text == "📞 Support":
        await update.message.reply_text(
            "📞 *24/7 VIP SUPPORT*\n\n"
            "Support ke liye contact karein:\n"
            "💬 Admin Support: @nobitabanxunban",
            parse_mode="Markdown"
        )

# ---------------------------------------------------------
# COMMANDS & INLINE CALLBACKS
# ---------------------------------------------------------
async def set_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id, update.effective_user.username)
    
    if not context.args:
        await update.message.reply_text("❌ Command syntax wrong!\nUse: `/setwallet YOUR_ADDRESS`", parse_mode="Markdown")
        return

    address = context.args[0]
    users_db[user_id]["wallet"] = address
    await update.message.reply_text(f"✅ *Wallet Address Saved Successfully!*\n\n`{address}`", parse_mode="Markdown")

async def inline_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "confirm_withdraw":
        bal = users_db[user_id]["balance"]
        wallet = users_db[user_id]["wallet"]
        
        if bal >= MIN_WITHDRAW:
            users_db[user_id]["balance"] = 0.0
            withdrawal_requests.append({"user_id": user_id, "amount": bal, "wallet": wallet})
            
            await query.answer("🚀 Processing Withdrawal...", show_alert=True)
            await query.edit_message_text(
                f"✅ *⚡ 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 𝗦𝗨𝗕𝗠𝗜𝗧𝗧𝗘𝗗! ⚡*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 *Amount:* `{bal:.4f} USDT`\n"
                f"👛 *Wallet:* `{wallet}`\n"
                f"⏳ *Status:* `Processing via Automatic Gateway`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📩 Payout complete hote hi notification mil jayega. Thank you!",
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ Insufficient Balance!", show_alert=True)

    elif data == "cancel_withdraw":
        await query.answer("Cancelled")
        await query.edit_message_text("❌ Withdrawal request cancelled.")

    elif data == "get_ref":
        ref_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}"
        await query.answer()
        await query.message.reply_text(f"🔗 *Your Referral Link:*\n`{ref_link}`", parse_mode="Markdown")

# ---------------------------------------------------------
# ADMIN COMMANDS (/stats & /broadcast)
# ---------------------------------------------------------
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Access Denied: Admin Only Command!")
        return

    total_users = len(users_db)
    verified_users = sum(1 for u in users_db.values() if u.get("joined"))
    total_balanced_usdt = sum(u.get("balance", 0) for u in users_db.values())

    stats_msg = (
        f"📊 *⚡ 𝗕𝗢𝗧 𝗔𝗗𝗠𝗜𝗡 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦 ⚡*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Total Registered Users:* `{total_users}`\n"
        f"✅ *Verified Active Users:* `{verified_users}`\n"
        f"💵 *Total User Balance:* `{total_balanced_usdt:.2f} USDT`\n"
        f"💸 *Pending Payout Requests:* `{len(withdrawal_requests)}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(stats_msg, parse_mode="Markdown")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Access Denied: Admin Only Command!")
        return

    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("❌ Usage: `/broadcast Your Text` ya kisi message/photo par reply karke `/broadcast` likhein.", parse_mode="Markdown")
        return

    users = list(users_db.keys())
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(f"⏳ *Broadcast Initiated to {len(users)} users...*", parse_mode="Markdown")

    for uid in users:
        try:
            if update.message.reply_to_message:
                await update.message.reply_to_message.copy(chat_id=uid)
            else:
                broadcast_text = " ".join(context.args)
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ *⚡ 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗 ⚡*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📤 *Successfully Sent:* `{sent}`\n"
        f"❌ *Failed / Blocked:* `{failed}`",
        parse_mode="Markdown"
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("setwallet", set_wallet_cmd))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_join"))
    app.add_handler(CallbackQueryHandler(inline_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("🤖 USDT Giveaway Bot is Online & Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
