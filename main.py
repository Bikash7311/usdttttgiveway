import logging
import asyncio
import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
)

# ---------------------------------------------------------
# FLASK KEEP-ALIVE SERVER (For Render Web Service)
# ---------------------------------------------------------
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "USDT Giveaway Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ---------------------------------------------------------
# BOT CONFIGURATION
# ---------------------------------------------------------
BOT_TOKEN = "8999949252:AAFajrj8WNlHWU9Px13VpltL2j1cPzyiPxY"
BOT_USERNAME = "@Usdt_giveway_bot"

ADMIN_IDS = [123456789]  # Replace with your numeric Telegram User ID

MANDATORY_CHANNEL = "@nobitabanxunban"
MANDATORY_CHANNEL_LINK = "https://t.me/nobitabanxunban"
PRIVATE_CHANNEL_LINK = "https://t.me/+ckvWhC-ac90zZTk1"

GIVEAWAY_PHOTO = "https://images.unsplash.com/photo-1621416894569-0f39ed31d247?w=1000"

MIN_WITHDRAW = 5.0
DAILY_BONUS = 0.05
REFERRAL_BONUS = 0.50

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
# MENU & WITHDRAWAL HANDLERS
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
            await update.message.reply_text("🎉 *DAILY REWARD CLAIMED!* 🎉\n\n✅ *+0.05 USDT* add ho gaya hai!", parse_mode="Markdown")
        else:
            await update.message.reply_text("⏳ *Bonus Already Claimed!* Kal wapas aana.", parse_mode="Markdown")

    elif text == "🔗 Referral Link":
        ref_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}"
        refs = users_db[user_id]["referrals"]
        
        caption = (
            f"🚀 *⚡ 𝗥𝗘𝗙𝗘𝗥 𝗔𝗡𝗗 𝗘𝗔𝗥𝗡 𝗨𝗦𝗗𝗧 ⚡*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 *Reward Per Refer:* `{REFERRAL_BONUS:.2f} USDT` 💎\n"
            f"👥 *Your Total Referrals:* `{refs}`\n\n"
            f"🔗 *Your Exclusive Invite Link:*\n`{ref_link}`"
        )
        keyboard = [[InlineKeyboardButton("📢 Share With Friends", url=f"https://t.me/share/url?url={ref_link}&text=Join%20USDT%20Giveaway%20Bot!")]]
        await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "⚙️ Set Wallet":
        await update.message.reply_text("⚙️ *SET WALLET*\n\nCommand send karein: `/setwallet YOUR_TRC20_ADDRESS`", parse_mode="Markdown")

    elif text == "💸 Premium Withdraw":
        bal = users_db[user_id]["balance"]
        wallet = users_db[user_id]["wallet"]
        
        if not wallet:
            await update.message.reply_text("⚠️ *Wallet Not Set!* Pehle `/setwallet ADDRESS` daalein.", parse_mode="Markdown")
            return

        if bal < MIN_WITHDRAW:
            needed = MIN_WITHDRAW - bal
            refs_needed = int((needed // REFERRAL_BONUS) + (1 if needed % REFERRAL_BONUS != 0 else 0))
            await update.message.reply_text(
                f"❌ *WITHDRAWAL LOCK DETECTED!*\n\n"
                f"💳 *Balance:* `{bal:.4f} USDT`\n"
                f"🎯 *Min. Limit:* `{MIN_WITHDRAW:.2f} USDT`\n"
                f"💡 Unlock karne ke liye *{refs_needed} aur refer* karein!",
                parse_mode="Markdown"
            )
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚡ Confirm & Instant Payout", callback_data="confirm_withdraw")],
                [InlineKeyboardButton("❌ Cancel Request", callback_data="cancel_withdraw")]
            ])
            await update.message.reply_text(
                f"👑 *⚡ 𝗨𝗦𝗗𝗧 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 ⚡*\n\n"
                f"💵 *Amount:* `{bal:.4f} USDT`\n"
                f"👛 *Wallet:* `{wallet}`\n\nConfirm karein?",
                parse_mode="Markdown", reply_markup=kb
            )

    elif text == "📊 Leaderboard":
        await update.message.reply_text("🏆 *TOP REFERRERS LEADERBOARD*\n\n1. @CryptoKing — 145 USDT\n2. @Alex — 92 USDT", parse_mode="Markdown")

    elif text == "📞 Support":
        await update.message.reply_text("💬 Admin Support: @nobitabanxunban")

async def set_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id, update.effective_user.username)
    if not context.args:
        await update.message.reply_text("❌ Usage: `/setwallet YOUR_ADDRESS`", parse_mode="Markdown")
        return
    users_db[user_id]["wallet"] = context.args[0]
    await update.message.reply_text(f"✅ *Wallet Address Saved!*\n`{context.args[0]}`", parse_mode="Markdown")

async def inline_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "confirm_withdraw":
        bal = users_db[user_id]["balance"]
        if bal >= MIN_WITHDRAW:
            users_db[user_id]["balance"] = 0.0
            withdrawal_requests.append({"user_id": user_id, "amount": bal, "wallet": users_db[user_id]["wallet"]})
            await query.answer("🚀 Processing...", show_alert=True)
            await query.edit_message_text("✅ *WITHDRAWAL REQUEST SUBMITTED!* Payout status update hone tak wait karein.", parse_mode="Markdown")
    elif query.data == "cancel_withdraw":
        await query.edit_message_text("❌ Request Cancelled.")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    await update.message.reply_text(f"📊 *STATS:* Total Users: `{len(users_db)}`", parse_mode="Markdown")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    users = list(users_db.keys())
    for uid in users:
        try:
            if update.message.reply_to_message:
                await update.message.reply_to_message.copy(chat_id=uid)
            else:
                await context.bot.send_message(chat_id=uid, text=" ".join(context.args), parse_mode="Markdown")
            await asyncio.sleep(0.05)
        except Exception: pass
    await update.message.reply_text("✅ Broadcast Completed!")

def main():
    # Run Web Keep-Alive for Render Web Service
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("setwallet", set_wallet_cmd))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_join"))
    app.add_handler(CallbackQueryHandler(inline_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("🤖 USDT Giveaway Bot with Flask Server is Online!")
    app.run_polling()

if __name__ == "__main__":
    main()
