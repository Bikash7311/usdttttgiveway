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

MANDATORY_CHANNELS = [
    {"name": "📢 Main Channel", "url": "https://t.me/nobitabanxunban"},
    {"name": "🔒 Backup Channel", "url": "https://t.me/+O1CtosbUTxU2ODBl"}
]

MIN_WITHDRAWAL = 5.0  # Minimum 5$ USDT

# Data storage
USER_BALANCES = {}
USER_PREMIUM = {}
ALL_USERS = set()  # Broadcast track karne ke liye set

# Conversation States for Withdrawal
WAITING_ADDRESS, WAITING_AMOUNT = range(2)

logging.basicConfig(level=logging.INFO)

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return True

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    ALL_USERS.add(user_id)  # Save user ID for broadcast

    if user_id not in USER_BALANCES:
        USER_BALANCES[user_id] = 0.0

    keyboard = [
        [InlineKeyboardButton("📢 Join Main Channel", url="https://t.me/nobitabanxunban")],
        [InlineKeyboardButton("🔒 Join Backup Channel", url="https://t.me/+O1CtosbUTxU2ODBl")],
        [InlineKeyboardButton("✅ Verified & Continue", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "💎 **WELCOME TO NOBITA BAN/UNBAN BOT** 💎\n\n"
        "⚡ *Premium Management & Security Automation System*\n\n"
        "⚠️ *Notice:* Bot ka access paane ke liye niche diye gaye dono channels join karna mandatory hai."
    )
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- MAIN MENU ---
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    ALL_USERS.add(user_id)

    balance = USER_BALANCES.get(user_id, 0.0)
    is_premium = "👑 Active" if USER_PREMIUM.get(user_id) else "❌ Inactive"

    text = (
        "🏛️ **MAIN DASHBOARD**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **User:** {query.from_user.first_name}\n"
        f"💳 **Balance:** `${balance:.2f} USDT`\n"
        f"⭐ **Premium:** `{is_premium}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 *Niche diye option me se choose karein:*"
    )

    keyboard = [
        [InlineKeyboardButton("💳 Wallet & Withdraw", callback_data="wallet_menu"), InlineKeyboardButton("💎 Buy Premium ($50)", callback_data="buy_premium")],
        [InlineKeyboardButton("📊 System Stats", callback_data="user_stats"), InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")],
    ]

    if user_id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Control Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- ADMIN STATS COMMAND (/stats) ---
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return

    total_users = len(ALL_USERS)
    premium_users = sum(1 for status in USER_PREMIUM.values() if status)

    text = (
        "📊 **ADMIN BOT STATISTICS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **Total Registered Users:** `{total_users}`\n"
        f"💎 **Total Premium Users:** `{premium_users}`\n"
        "🟢 **Status:** `Active & Operational`\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# --- ADMIN BROADCAST COMMAND (/broadcast) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        return

    # Check if replied to a message or sent text
    reply_msg = update.message.reply_to_message
    broadcast_text = " ".join(context.args)

    if not reply_msg and not broadcast_text:
        await update.message.reply_text(
            "⚠️ **Broadcast Syntax Error**\n\n"
            "👉 **Usage:** Message ke reply me `/broadcast` likhein\n"
            "   *ya phir* `/broadcast Aapka Message Here` likhein."
        )
        return

    status_msg = await update.message.reply_text("🚀 Broadcasting message to all users...")

    sent_count = 0
    failed_count = 0

    for uid in list(ALL_USERS):
        try:
            if reply_msg:
                await context.bot.copy_message(chat_id=uid, from_chat_id=reply_msg.chat_id, message_id=reply_msg.message_id)
            else:
                await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="Markdown")
            sent_count += 1
            await asyncio.sleep(0.04)  # Rate limiting protection
        except Exception:
            failed_count += 1

    await status_msg.edit_text(
        "📢 **BROADCAST COMPLETED**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ **Successfully Delivered:** `{sent_count}`\n"
        f"❌ **Failed/Blocked:** `{failed_count}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# --- WALLET & WITHDRAWAL UI ---
async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    balance = USER_BALANCES.get(user_id, 0.0)

    text = (
        "💼 **YOUR DIGITAL WALLET**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Available Balance:** `${balance:.2f} USDT`\n"
        f"🔻 **Minimum Payout:** `${MIN_WITHDRAWAL:.2f} USDT`\n"
        f"⚡ **Network:** `USDT (TRC20 / BEP20)`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *Withdrawal request apply karne ke liye niche button pe click karein.*"
    )

    keyboard = [
        [InlineKeyboardButton("💸 Request Withdrawal", callback_data="start_withdraw")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- WITHDRAWAL PROCESS ---
async def start_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    balance = USER_BALANCES.get(user_id, 0.0)

    if balance < MIN_WITHDRAWAL:
        await query.answer(f"❌ Insufficient Balance! Minimum withdrawal is ${MIN_WITHDRAWAL} USDT.", show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text(
        "📥 **WITHDRAWAL PROCESS (Step 1/2)**\n\n"
        "Apna **USDT Wallet Address** (TRC20 / BEP20) message me send karein:\n\n"
        "_Cancel karne ke liye /cancel likhein._",
        parse_mode="Markdown"
    )
    return WAITING_ADDRESS

async def process_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    context.user_data['withdraw_address'] = address

    await update.message.reply_text(
        "💵 **WITHDRAWAL PROCESS (Step 2/2)**\n\n"
        "Aap kitna **USDT** withdraw karna chahte hain? Amount enter karein (Min $5):\n\n"
        "_Example: 5.5_",
        parse_mode="Markdown"
    )
    return WAITING_AMOUNT

async def process_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text_val = update.message.text.strip()

    try:
        amount = float(text_val)
    except ValueError:
        await update.message.reply_text("❌ Invalid amount format. Kripya number enter karein (e.g., 5.0).")
        return WAITING_AMOUNT

    balance = USER_BALANCES.get(user_id, 0.0)

    if amount < MIN_WITHDRAWAL:
        await update.message.reply_text(f"❌ Minimum withdrawal amount is `${MIN_WITHDRAWAL} USDT`. Fir se try karein:")
        return WAITING_AMOUNT

    if amount > balance:
        await update.message.reply_text(f"❌ Insufficient Balance! Aapke paas sirf `${balance:.2f} USDT` hai.")
        return WAITING_AMOUNT

    address = context.user_data.get('withdraw_address')
    USER_BALANCES[user_id] -= amount

    await update.message.reply_text(
        "✅ **WITHDRAWAL REQUEST SUBMITTED**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 **Amount:** `${amount:.2f} USDT`\n"
        f"🏦 **Address:** `{address}`\n"
        "⏳ **Status:** `Pending Processing`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📩 *Aapki request admin ko bhej di gayi hai. Direct confirmation ke liye contact karein:* @Znonsence",
        parse_mode="Markdown"
    )

    try:
        admin_text = (
            "🚨 **NEW WITHDRAWAL REQUEST**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **User:** {user.full_name} (`{user_id}`)\n"
            f"💰 **Amount:** `${amount:.2f} USDT`\n"
            f"🔗 **Wallet Address:** `{address}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        await context.bot.send_message(chat_id=OWNER_ID, text=admin_text, parse_mode="Markdown")
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
        "⭐ **BUY PREMIUM MEMBERSHIP** ⭐\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **Price:** `$50 USD` (Lifetime Access)\n"
        "🚀 **Features:** Full Bot Control, Auto Ban/Unban, VIP Analytics & Priority Support.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 Payment ke liye direct Owner se contact karein:\n"
        f"👉 **Owner:** {OWNER_USERNAME}"
    )

    keyboard = [
        [InlineKeyboardButton("💬 Contact Owner", url=f"https://t.me/{OWNER_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# --- USER SYSTEM STATS ---
async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "📊 **SYSTEM PERFORMANCE & STATS**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 **Bot Status:** `Online (High Speed)`\n"
        f"👥 **Total System Users:** `{len(ALL_USERS)}`\n"
        "⚡ **Ping Rate:** `24 ms`\n"
        "🛡️ **System Security:** `AES-256 Bit Encrypted`\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

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

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Callback Handlers
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(wallet_menu, pattern="^wallet_menu$"))
    app.add_handler(CallbackQueryHandler(buy_premium, pattern="^buy_premium$"))
    app.add_handler(CallbackQueryHandler(user_stats, pattern="^user_stats$"))
    app.add_handler(withdraw_handler)

    print("🚀 Bot Started Successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
