import telebot
from telebot import types

# 🔑 Config
TOKEN = "8392518590:AAHiUPI_STP3m8ewY6jGLfvV7Wc-kGbx_h4"
ADMIN_ID = 7845479937
CHANNEL = "@freekasearch2"
PAYOUT_CHANNEL = "@BOTxPAYOUTS"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Fake DB for demo (replace with database later)
user_balance = {}
user_referrals = {}

# 🔹 Helper: check subscription
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🔹 /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ Joined", callback_data="joined"))
        bot.send_message(user_id, "👋 Welcome!\n\n⚠️ Please join our official channel to use this bot.", reply_markup=markup)
        return

    if user_id not in user_balance:
        user_balance[user_id] = 0

    bot.send_message(
        user_id,
        f"👋 Hello <b>{message.from_user.first_name}</b>!\n\n"
        "🎉 Welcome to our Referral Bot.\n\n"
        "💰 Earn rewards by inviting friends and use menu below to check balance or withdraw.",
    )
    show_main_menu(user_id)

@bot.callback_query_handler(func=lambda call: call.data == "joined")
def joined_channel(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "⚠️ Please join the channel first.")

# 🔹 Main Menu
def show_main_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("💰 Balance", "👫 Invite")
    keyboard.row("📊 Statistics", "📤 Withdraw")
    bot.send_message(chat_id, "🏠 Main Menu", reply_markup=keyboard)

# 🔹 Balance
@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    bal = user_balance.get(message.from_user.id, 0)
    bot.send_message(message.chat.id, f"💰 Your Balance: <b>{bal}</b> coins")

# 🔹 Invite
@bot.message_handler(func=lambda m: m.text == "👫 Invite")
def invite(message):
    user_id = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(message.chat.id, f"🔗 Your referral link:\n{link}")

# 🔹 Statistics
@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def stats(message):
    uid = message.from_user.id
    refs = user_referrals.get(uid, 0)
    bal = user_balance.get(uid, 0)
    bot.send_message(message.chat.id, f"📊 Stats:\n👫 Referrals: {refs}\n💰 Balance: {bal}")

# 🔹 Withdraw
@bot.message_handler(func=lambda m: m.text == "📤 Withdraw")
def withdraw(message):
    bot.send_message(message.chat.id, "💸 Enter amount to withdraw (Min 10, Max 15):")
    bot.register_next_step_handler(message, process_withdraw)

def process_withdraw(message):
    uid = message.from_user.id
    try:
        amt = int(message.text)
        if amt < 10 or amt > 15:
            bot.send_message(uid, "⚠️ Withdrawal amount must be between 10 and 15.")
            return

        if user_balance.get(uid, 0) < amt:
            bot.send_message(uid, "❌ Insufficient balance.")
            return

        user_balance[uid] -= amt

        # User confirmation
        bot.send_message(uid, f"✅ Withdrawal request of {amt} coins submitted!\n\n📢 Check updates here: {PAYOUT_CHANNEL}")

        # Send to payouts channel with Approve/Reject buttons
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Approve", callback_data=f"approve:{uid}:{amt}"))
        markup.add(types.InlineKeyboardButton("❌ Reject", callback_data=f"reject:{uid}:{amt}"))

        bot.send_message(
            PAYOUT_CHANNEL,
            f"💸 <b>New Withdrawal Request!</b>\n\n👤 User ID: <code>{uid}</code>\n💰 Amount: {amt}",
            reply_markup=markup
        )

    except:
        bot.send_message(uid, "⚠️ Invalid input. Please try again.")

# 🔹 Handle Approve/Reject
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve") or call.data.startswith("reject"))
def handle_admin_actions(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "⛔ You are not authorized!")
        return

    action, uid, amt = call.data.split(":")
    uid = int(uid)
    amt = int(amt)

    if action == "approve":
        bot.edit_message_text(
            f"✅ Withdrawal Approved!\n\n👤 User ID: <code>{uid}</code>\n💰 Amount: {amt}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(uid, f"🎉 Your withdrawal of {amt} coins has been approved and processed!")

    elif action == "reject":
        bot.edit_message_text(
            f"❌ Withdrawal Rejected!\n\n👤 User ID: <code>{uid}</code>\n💰 Amount: {amt}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(uid, f"⚠️ Your withdrawal of {amt} coins has been rejected by admin.")

    bot.answer_callback_query(call.id, "✅ Action completed.")

# 🔹 Admin Panel
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Unauthorized")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"))
    bot.send_message(message.chat.id, "⚙️ Admin Panel", reply_markup=markup)

# 🔹 Polling
print("🤖 Bot running...")
bot.infinity_polling()
