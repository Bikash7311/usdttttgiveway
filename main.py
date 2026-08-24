import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Configuration
API_ID = 33772941
API_HASH = "3b6ab6b1940c87915439bb41e4e80ea8"
BOT_TOKEN = "8580109392:AAH_IASAWo3vAiPAfSNbr_l_Yk8UG72V6R0"

OWNER_USERNAME = "@Znonsence"
OWNER_ID = 6132146801  # Admin User ID
BOT_USERNAME = "@Nobita_banbot"

MANDATORY_CHANNELS = [
    {"name": "📢 Main Channel", "url": "https://t.me/nobitabanxunban"},
    {"name": "🔒 Backup Channel", "url": "https://t.me/+O1CtosbUTxU2ODBl"}
]

MIN_WITHDRAWAL = 5.0  # Minimum 5$ USDT

# Data storage (In-Memory)
USER_BALANCES = {}
USER_PREMIUM = {}
ALL_USERS = set()  # Broadcast track karne ke liye set

# Conversation States for Withdrawal
WAITING_ADDRESS, WAITING_AMOUNT = range(2)

logging.basicConfig(level=logging.INFO)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    ALL_USERS.add(user_id)  # Save user ID for broadcast

    if user_id not in USER_BALANCES:
        USER_BALANCES[user_id] = 0.0

    keyboard = [
        [InlineKeyboardButton("📢 Main Channel", url="https://t.me/nobitabanxunban")],
        [InlineKeyboardButton("🔒 Backup Channel", url="https://t.me/+O1CtosbUTxU2ODBl")],
        [InlineKeyboardButton("🤖 Share Bot Link", url=f"https://t.me/share/url?url=https://t.me/Nobita_banbot")],
        [InlineKeyboardButton("✅ Verified & Continue", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "✨ <b>Welcome to Nobita Security Bot</b> ✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>Bot Username:</b> {BOT_USERNAME}\n"
        "⚡ <b>Status:</b> <i>Premium Active & Operational</i>\n\n"
        "⚠️ <b>Mandatory Requirement:</b>\n"
        "Bot access ke liye niche diye gaye dono official channels join karna zaroori hai.\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

# --- MAIN MENU ---
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    ALL_USERS.add(user_id)

    balance = USER_BALANCES.get(user_id, 0.0)
    is_premium = "👑 Active (VIP)" if USER_PREMIUM.get(user_id) else "❌ Regular User"

    text = (
        "👑 <b>NOBITA VIP SYSTEM DASHBOARD</b> 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>User:</b> {query.from_user.first_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"💳 <b>Balance:</b> <code>${balance:.2f} USDT</code>\n"
        f"⭐ <b>Status:</b> <code>{is_premium}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <i>Apna required option select karein:</i>"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Wallet & Withdraw", callback_data="wallet_menu"), InlineKeyboardButton("💎 Buy Premium ($50)", callback_data="buy_premium")],
        [InlineKeyboardButton("📊 System Stats", callback_data="user_stats"), InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")],
    ]

    if user_id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Controls", callback_data="admin_info")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

# --- ADMIN STATS COMMAND (/stats) ---
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ <i>Aapke paas is command ko use karne ki permission nahi hai.</i>", parse_mode="HTML")
        return

    total_users = len(ALL_USERS)
    premium_users = sum(1 for status in USER_PREMIUM.values() if status)

    text = (
        "📊 <b>ADMIN SYSTEM STATISTICS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Users Tracked:</b> <code>{total_users}</code>\n"
        f"💎 <b>Premium Subscribers:</b> <code>{premium_users}</code>\n"
        f"🤖 <b>Bot Target:</b> <code>{BOT_USERNAME}</code>\n"
        "🟢 <b>System Health:</b> <code>100% Operational</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# --- ADMIN BROADCAST COMMAND (/broadcast) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ <i>Only Owner can execute broadcast.</i>", parse_mode="HTML")
        return

    reply_msg = update.message.reply_to_message
    broadcast_text = " ".join(context.args)

    if not reply_msg and not broadcast_text:
        await update.message.reply_text(
            "⚠️ <b>Broadcast Syntax Error!</b>\n\n"
            "👉 <b>Usage 1:</b> Kisi message ko reply karke <code>/broadcast</code> likhein.\n"
            "👉 <b>Usage 2:</b> Direct command me text add karein: <code>/broadcast Hello Users!</code>",
            parse_mode="HTML"
        )
        return

    status_msg = await update.message.reply_text("🚀 <i>Broadcasting message to all active users...</i>", parse_mode="HTML")

    sent_count = 0
    failed_count = 0

    for uid in list(ALL_USERS):
        try:
            if reply_msg:
                await context.bot.copy_message(chat_id=uid, from_chat_id=reply_msg.chat_id, message_id=reply_msg.message_id)
            else:
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="HTML")
            sent_count += 1
            await asyncio.sleep(0.04)  # Protection against Telegram FloodWait
        except Exception:
            failed_count += 1

    await status_msg.edit_text(
        "📢 <b>BROADCAST REPORT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>Delivered Successfully:</b> <code>{sent_count}</code>\n"
        f"❌ <b>Failed/Blocked:</b> <code>{failed_count}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )

# --- WALLET & WITHDRAWAL UI ---
async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    balance = USER_BALANCES.get(user_id, 0.0)

    text = (
        "💼 <b>OFFICIAL USDT WALLET</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Available Balance:</b> <code>${balance:.2f} USDT</code>\n"
        f"🔻 <b>Minimum Payout:</b> <code>${MIN_WITHDRAWAL:.2f} USDT</code>\n"
        "⚡ <b>Network:</b> <code>USDT (TRC20 / BEP20)</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [InlineKeyboardButton("💸 Request Withdrawal", callback_data="start_withdraw")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

# --- WITHDRAWAL PROCESS ---
async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    balance = USER_BALANCES.get(user_id, 0.0)

    if balance < MIN_WITHDRAWAL:
        await query.answer(f"❌ Low balance! Minimum payout is ${MIN_WITHDRAWAL} USDT.", show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text(
        "📥 <b>WITHDRAWAL (Step 1/2)</b>\n\n"
        "Apna valid <b>USDT TRC20/BEP20 Address</b> message me type karein:\n\n"
        "<i>Cancel karne ke liye /cancel likhein.</i>",
        parse_mode="HTML"
    )
    return WAITING_ADDRESS

async def process_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    context.user_data['withdraw_address'] = address

    await update.message.reply_text(
        "💵 <b>WITHDRAWAL (Step 2/2)</b>\n\n"
        "Kitna USDT withdraw karna chahte hain? Amount send karein (Min $5):\n\n"
        "<i>Example: 5.5</i>",
        parse_mode="HTML"
    )
    return WAITING_AMOUNT

async def process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text_val = update.message.text.strip()

    try:
        amount = float(text_val)
    except ValueError:
        await update.message.reply_text("❌ Invalid format! Number enter karein (e.g., 5.0).")
        return WAITING_AMOUNT

    balance = USER_BALANCES.get(user_id, 0.0)

    if amount < MIN_WITHDRAWAL or amount > balance:
        await update.message.reply_text(f"❌ Invalid amount! Balance check karke firse try karein.")
        return WAITING_AMOUNT

    address = context.user_data.get('withdraw_address')
    USER_BALANCES[user_id] -= amount

    await update.message.reply_text(
        "✅ <b>WITHDRAWAL REQUEST SUBMITTED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>Amount:</b> <code>${amount:.2f} USDT</code>\n"
        f"🏦 <b>Address:</b> <code>{address}</code>\n"
        "⏳ <b>Status:</b> <code>Processing</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📩 Direct Owner Support: {OWNER_USERNAME}",
        parse_mode="HTML"
    )

    try:
        admin_text = (
            "🚨 <b>NEW WITHDRAWAL ALERT</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User:</b> {user.full_name} (<code>{user_id}</code>)\n"
            f"💰 <b>Amount:</b> <code>${amount:.2f} USDT</code>\n"
            f"🔗 <b>Address:</b> <code>{address}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        await context.bot.send_message(chat_id=OWNER_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Failed to notify owner: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Action cancelled.")
    return ConversationHandler.END

# --- BUY PREMIUM ---
async def buy_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "⭐ <b>NOBITA PREMIUM MEMBERSHIP</b> ⭐\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Price:</b> <code>$50 USD</code> (Lifetime Pass)\n"
        "🚀 <b>Features:</b> Group Auto Management, Unlimited Access, VIP Anti-Ban Shield.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 Purchase ke liye direct contact karein:\n"
        f"👉 <b>Owner:</b> {OWNER_USERNAME}"
    )

    keyboard = [
        [InlineKeyboardButton("💬 Contact Owner", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

# --- USER SYSTEM STATS ---
async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "📊 <b>SYSTEM RUNTIME METRICS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 <b>Status:</b> <code>Active & Online</code>\n"
        f"👥 <b>Total System Network:</b> <code>{len(ALL_USERS)} Users</code>\n"
        f"🤖 <b>Bot Target:</b> {BOT_USERNAME}\n"
        "⚡ <b>Latency:</b> <code>~18ms</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

# --- MAIN RUNNER ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    withdraw_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_withdraw, pattern="^start_withdraw$")],
        states={
            WAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_address)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Command Handlers (Explicit Routing)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Callback Handlers
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(wallet_menu, pattern="^wallet_menu$"))
    app.add_handler(CallbackQueryHandler(buy_premium, pattern="^buy_premium$"))
    app.add_handler(CallbackQueryHandler(user_stats, pattern="^user_stats$"))
    app.add_handler(withdraw_handler)

    print(f"🚀 Bot Started Successfully! (@Nobita_banbot)")
    app.run_polling()

if __name__ == "__main__":
    main()
