import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANIME_CHANNEL = int(os.environ.get("ANIME_CHANNEL", "0"))
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)

def load_channels():
    if os.path.exists("channels.json"):
        with open("channels.json", "r") as f:
            return json.load(f)
    return []

def save_channels(channels):
    with open("channels.json", "w") as f:
        json.dump(channels, f)

def load_view():
    if os.path.exists("view.json"):
        with open("view.json", "r") as f:
            return json.load(f)
    return {}

def save_view(data):
    with open("view.json", "w") as f:
        json.dump(data, f)

required_channels = load_channels()
view_channels = load_view()

def check_subscription(user_id):
    not_subbed = []
    for channel in required_channels:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                not_subbed.append(channel)
        except:
            not_subbed.append(channel)
    return not_subbed

def sub_keyboard(channels):
    markup = InlineKeyboardMarkup()
    for ch in channels:
        try:
            chat = bot.get_chat(ch)
            link = chat.invite_link or f"https://t.me/{chat.username}"
            markup.add(InlineKeyboardButton("📢 Obuna bo'lish", url=link))
        except:
            pass
    markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "👋 Salom! Anime kodini yuboring 👇\n\n"
        "Kod — kanal postining oxiridagi raqam")

@bot.message_handler(commands=['addchannel'])
def add_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /addchannel -1001234567890")
        return
    ch_id = int(parts[1])
    if ch_id not in required_channels:
        required_channels.append(ch_id)
        save_channels(required_channels)
        bot.send_message(message.chat.id, "✅ Kanal qo'shildi!")
    else:
        bot.send_message(message.chat.id, "Bu kanal allaqachon bor!")

@bot.message_handler(commands=['removechannel'])
def remove_channel(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /removechannel -1001234567890")
        return
    ch_id = int(parts[1])
    if ch_id in required_channels:
        required_channels.remove(ch_id)
        save_channels(required_channels)
        bot.send_message(message.chat.id, "✅ Kanal o'chirildi!")
    else:
        bot.send_message(message.chat.id, "Bu kanal topilmadi!")

@bot.message_handler(commands=['listchannels'])
def list_channels(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not required_channels:
        bot.send_message(message.chat.id, "Hozircha kanal yo'q")
    else:
        text = "📋 Majburiy kanallar:\n"
        for ch in required_channels:
            text += f"• {ch}\n"
        bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['addview'])
def add_view(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id, "Format: /addview 1 https://t.me/+xxx")
        return
    code = parts[1]
    link = parts[2]
    view_channels[code] = link
    save_view(view_channels)
    bot.send_message(message.chat.id, f"✅ Ko'rish qo'shildi! Kod: {code}")

@bot.message_handler(commands=['removeview'])
def remove_view(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /removeview 1")
        return
    code = parts[1]
    if code in view_channels:
        del view_channels[code]
        save_view(view_channels)
        bot.send_message(message.chat.id, "✅ O'chirildi!")
    else:
        bot.send_message(message.chat.id, "❌ Topilmadi!")

@bot.message_handler(commands=['listview'])
def list_view(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not view_channels:
        bot.send_message(message.chat.id, "Hozircha yo'q")
    else:
        text = "📋 Ko'rish kanallari:\n"
        for code, link in view_channels.items():
            text += f"• {code} → {link}\n"
        bot.send_message(message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    not_sub = check_subscription(call.from_user.id)
    if not_sub:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!")
    else:
        bot.answer_callback_query(call.id, "✅ Rahmat!")
        bot.send_message(call.message.chat.id, "Endi kod yuboring 👇")

@bot.message_handler(func=lambda m: True)
def handle_code(message):
    not_sub = check_subscription(message.from_user.id)
    if not_sub:
        bot.send_message(message.chat.id,
            "⚠️ Botdan foydalanish uchun kanallarga obuna bo'ling!",
            reply_markup=sub_keyboard(not_sub))
        return
    try:
        code = message.text.strip()
        if code in view_channels:
            link = view_channels[code]
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("👁 Ko'rish", url=link))
            bot.send_message(message.chat.id, "👇 Ko'rish uchun bosing:", reply_markup=markup)
        else:
            post_id = int(code)
            bot.forward_message(message.chat.id, ANIME_CHANNEL, post_id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Faqat raqam yuboring!")
    except Exception:
        bot.send_message(message.chat.id, "❌ Bunday kod topilmadi!")

bot.infinity_polling(timeout=10, long_polling_timeout=5)
