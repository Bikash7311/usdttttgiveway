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
BOT_TOKEN = "8999949252:AAHxaZv45n6b1Nfzl8xr61XiNW19uZwQuZE"
BOT_USERNAME = "@Nobita_banbot"

ADMIN_IDS = [6132146801]  # Updated with Admin User ID

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
        [InlineKeyboardButton("🤖 Mandatory Bot Link", url=f"https://t.me/{BOT_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("⚡ 3️⃣ VERIFY & CLAIM REWARDS ⚡", callback_data="verify_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"👑 <b>⚡ 𝗛𝗘𝗬𝗬 {first_name.upper()} ⚡</b>\n\n"
        f"🔥 <b>𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗨𝗦𝗗𝗧 𝗚𝗜𝗩𝗘𝗔𝗪𝗔𝗬 𝗕𝗢𝗧</b> 🔥\n"
        f"🤖 <b>Bot Link:</b> {BOT_USERNAME}\n\n"
        f"🏆 <b>💎 Premium USDT Rewards System 💎</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 <b>Daily Bonus:</b> <code>{DAILY_BONUS:.2f} USDT</code> / 24 Hours\n"
        f"👥 <b>Per Referral:</b> <code>{REFERRAL_BONUS:.2f} USDT</code> (Instant)\n"
        f"💸 <b>Min. Payout:</b> <code>{MIN_WITHDRAW:.2f} USDT</code> (BEP20 / TRC20)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👇 <i>Niche diye gaye channels join karein aur Verify button par click karein!</i>"
    )

    await update.message.reply_photo(
        photo=GIVEAWAY_PHOTO,
        caption=caption,
        parse_mode="HTML",
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
                            f"🎉 <b>New Referral Joined!</b>\n\n"
                            f"👤 User: <code>{query.from_user.first_name}</code>\n"
                            f"➕ Added: <code>+{REFERRAL_BONUS:.2f} USDT</code> 💎"
                        ),
                        parse_mode="HTML"
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
        f"🌟 <b>WELCOME TO DASHBOARD, {name.upper()}!</b> 🌟\n\n"
        f"✅ Aapka account verified hai.\n"
        f"🤖 Bot: {BOT_USERNAME}\n"
        f"🚀 Niche Menu se Option select karein aur USDT earn karna shuru karein!"
    )
    await message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

# ---------------------------------------------------------
# MENU & WITHDRAWAL HANDLERS
# ---------------------------------------------------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    init_user(user_id, update.effective_user.username)

    if not users_db[user_id]["joined"]:
        await update.message.reply_text("⚠️ Pehle <code>/start</code> dabakar channels verify karein!", parse_mode="HTML")
        return

    if text == "💰 Balance":
        bal = users_db[user_id]["balance"]
        refs = users_db[user_id]["referrals"]
        wallet = users_db[user_id]["wallet"] or "Not Set (⚙️ Set Wallet par click karein)"
        
        reply = (
            f"💳 <b>⚡ 𝗬𝗢𝗨𝗥 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 ⚡</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> <code>{update.effective_user.first_name}</code>\n"
            f"💵 <b>USDT Balance:</b> <code>{bal:.4f} USDT</code> 💎\n"
            f"👥 <b>Total Referrals:</b> <code>{refs} Users</code> 🔥\n"
            f"👛 <b>Configured Wallet:</b> <code>{wallet}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Next Goal:</b> Minimum <code>{MIN_WITHDRAW:.2f} USDT</code> to Payout!"
        )
        await update.message.reply_text(reply, parse_mode="HTML")

    elif text == "🎁 Daily Bonus":
        if not users_db[user_id]["claimed_today"]:
            users_db[user_id]["balance"] += DAILY_BONUS
            users_db[user_id]["claimed_today"] = True
            await update.message.reply_text("🎉 <b>DAILY REWARD CLAIMED!</b> 🎉\n\n✅ <b>+0.05 USDT</b> add ho gaya hai!", parse_mode="HTML")
        else:
            await update.message.reply_text("⏳ <b>Bonus Already Claimed!</b> Kal wapas aana.", parse_mode="HTML")

    elif text == "🔗 Referral Link":
        ref_link = f"https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}"
        refs = users_db[user_id]["referrals"]
        
        caption = (
            f"🚀 <b>⚡ 𝗥𝗘𝗙𝗘𝗥 𝗔𝗡𝗗 𝗘𝗔𝗥𝗡 𝗨𝗦𝗗𝗧 ⚡</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 <b>Reward Per Refer:</b> <code>{REFERRAL_BONUS:.2f} USDT</code> 💎\n"
            f"👥 <b>Your Total Referrals:</b> <code>{refs}</code>\n\n"
            f"🔗 <b>Your Exclusive Invite Link:</b>\n<code>{ref_link}</code>"
        )
        keyboard = [[InlineKeyboardButton("📢 Share With Friends", url=f"https://t.me/share/url?url={ref_link}&text=Join%20USDT%20Giveaway%20Bot!")]]
        await update.message.reply_text(caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "⚙️ Set Wallet":
        await update.message.reply_text("⚙️ <b>SET WALLET</b>\n\nCommand send karein: <code>/setwallet YOUR_TRC20_ADDRESS</code>", parse_mode="HTML")

    elif text == "💸 Premium Withdraw":
        bal = users_db[user_id]["balance"]
        wallet = users_db[user_id]["wallet"]
        
        if not wallet:
            await update.message.reply_text("⚠️ <b>Wallet Not Set!</b> Pehle <code>/setwallet ADDRESS</code> daalein.", parse_mode="HTML")
            return

        if bal < MIN_WITHDRAW:
            needed = MIN_WITHDRAW - bal
            refs_needed = int((needed // REFERRAL_BONUS) + (1 if needed % REFERRAL_BONUS != 0 else 0))
            await update.message.reply_text(
                f"❌ <b>WITHDRAWAL LOCK DETECTED!</b>\n\n"
                f"💳 <b>Balance:</b> <code>{bal:.4f} USDT</code>\n"
                f"🎯 <b>Min. Limit:</b> <code>{MIN_WITHDRAW:.2f} USDT</code>\n"
                f"💡 Unlock karne ke liye <b>{refs_needed} aur refer</b> karein!",
                parse_mode="HTML"
            )
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚡ Confirm & Instant Payout", callback_data="confirm_withdraw")],
                [InlineKeyboardButton("❌ Cancel Request", callback_data="cancel_withdraw")]
            ])
            await update.message.reply_text(
                f"👑 <b>⚡ 𝗨𝗦𝗗𝗧 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪𝗔𝗟 ⚡</b>\n\n"
                f"💵 <b>Amount:</b> <code>{bal:.4f} USDT</code>\n"
                f"👛 <b>Wallet:</b> <code>{wallet}</code>\n\nConfirm karein?",
                parse_mode="HTML", reply_markup=kb
            )

    elif text == "📊 Leaderboard":
        await update.message.reply_text("🏆 <b>TOP REFERRERS LEADERBOARD</b>\n\n1. @CryptoKing — 145 USDT\n2. @Alex — 92 USDT", parse_mode="HTML")

    elif text == "📞 Support":
        await update.message.reply_text("💬 Admin Support: @nobitabanxunban", parse_mode="HTML")

async def set_wallet_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    init_user(user_id, update.effective_user.username)
    if not context.args:
        await update.message.reply_text("❌ Usage: <code>/setwallet YOUR_ADDRESS</code>", parse_mode="HTML")
        return
    users_db[user_id]["wallet"] = context.args[0]
    await update.message.reply_text(f"✅ <b>Wallet Address Saved!</b>\n<code>{context.args[0]}</code>", parse_mode="HTML")

async def inline_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "confirm_withdraw":
        bal = users_db[user_id]["balance"]
        if bal >= MIN_WITHDRAW:
            users_db[user_id]["balance"] = 0.0
            withdrawal_requests.append({"user_id": user_id, "amount": bal, "wallet": users_db[user_id]["wallet"]})
            await query.answer("🚀 Processing...", show_alert=True)
            await query.edit_message_text("✅ <b>WITHDRAWAL REQUEST SUBMITTED!</b> Payout status update hone tak wait karein.", parse_mode="HTML")
    elif query.data == "cancel_withdraw":
        await query.edit_message_text("❌ Request Cancelled.")

# ---------------------------------------------------------
# ADMIN COMMANDS (/stats & /broadcast)
# ---------------------------------------------------------
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ <i>Access Denied!</i>", parse_mode="HTML")
        return

    text = (
        "📊 <b>ADMIN SYSTEM STATISTICS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Users:</b> <code>{len(users_db)}</code>\n"
        f"🤖 <b>Bot Target:</b> <code>{BOT_USERNAME}</code>\n"
        f"💳 <b>Pending Withdrawals:</b> <code>{len(withdrawal_requests)}</code>\n"
        "🟢 <b>Status:</b> <code>100% Active</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ <i>Only Admin can use broadcast.</i>", parse_mode="HTML")
        return

    reply_msg = update.message.reply_to_message
    broadcast_text = " ".join(context.args)

    if not reply_msg and not broadcast_text:
        await update.message.reply_text(
            "⚠️ <b>Broadcast Syntax Error!</b>\n\n"
            "👉 <b>Usage 1:</b> Message reply karke <code>/broadcast</code> likhein.\n"
            "👉 <b>Usage 2:</b> Direct command: <code>/broadcast Hello Users!</code>",
            parse_mode="HTML"
        )
        return

    status_msg = await update.message.reply_text("🚀 <i>Broadcasting message to all users...</i>", parse_mode="HTML")

    sent_count = 0
    failed_count = 0

    for uid in list(users_db.keys()):
        try:
            if reply_msg:
                await context.bot.copy_message(chat_id=uid, from_chat_id=reply_msg.chat_id, message_id=reply_msg.message_id)
            else:
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed_count += 1

    await status_msg.edit_text(
        "📢 <b>BROADCAST COMPLETED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Delivered:</b> <code>{sent_count}</code>\n"
        f"❌ <b>Failed:</b> <code>{failed_count}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
def main():
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("setwallet", set_wallet_cmd))

    # Callback & Message Handlers
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_join$"))
    app.add_handler(CallbackQueryHandler(inline_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("🤖 USDT Giveaway Bot is Online!")
    app.run_polling()

if __name__ == "__main__":
    main()
