import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8824206791:AAFbsQUeDE6X8S3FF8hozaQq5V4--ZWAYgw"
ANIME_CHANNEL = -1003834530984
ADMIN_ID = 8485318962

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== FAYLLARNI YUKLASH/SAQLASH ====================

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

required_channels = load_json("channels.json", [])
view_channels = load_json("view.json", {})
anime_channels = load_json("anime_channels.json", {})  # {kod: kanal_id}
users = load_json("users.json", {})
banned_users = load_json("banned.json", [])

# ==================== YORDAMCHI FUNKSIYALAR ====================

def register_user(user):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
        save_json("users.json", users)

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

def get_all_message_ids(channel_id):
    """Kanaldagi barcha xabar IDlarini olish"""
    ids = []
    try:
        # Kanalning eng oxirgi xabarini topamiz
        chat = bot.get_chat(channel_id)
        # Oxirgi post IDni topish uchun yuqori chegaradan qidirish
        # Telegram API orqali forward qilib tekshiramiz
        for i in range(1, 10000):
            try:
                msg = bot.forward_message(chat_id=ADMIN_ID, from_chat_id=channel_id, message_id=i, disable_notification=True)
                ids.append(i)
                bot.delete_message(ADMIN_ID, msg.message_id)
            except:
                pass
    except:
        pass
    return ids

# ==================== OBUNA TEKSHIRISH ====================

@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_callback(call):
    not_sub = check_subscription(call.from_user.id)
    if not_sub:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!")
    else:
        bot.answer_callback_query(call.id, "✅ Rahmat!")
        bot.send_message(call.message.chat.id, "✅ Obuna tasdiqlandi! Endi kod yuboring 👇")

# ==================== ANIME SAHIFALASH ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("anime_next:") or call.data.startswith("anime_prev:"))
def anime_page_callback(call):
    parts = call.data.split(":")
    action = parts[0]
    channel_id = int(parts[1])
    current_id = int(parts[2])
    max_id = int(parts[3])

    if action == "anime_next":
        next_id = current_id + 1
        # Keyingi mavjud postni topamiz
        found = False
        for msg_id in range(next_id, max_id + 1):
            try:
                markup = InlineKeyboardMarkup()
                if msg_id < max_id:
                    markup.add(
                        InlineKeyboardButton("⬅️ Oldingi", callback_data=f"anime_prev:{channel_id}:{msg_id}:{max_id}"),
                        InlineKeyboardButton("Keyingisi ➡️", callback_data=f"anime_next:{channel_id}:{msg_id}:{max_id}")
                    )
                else:
                    markup.add(
                        InlineKeyboardButton("⬅️ Oldingi", callback_data=f"anime_prev:{channel_id}:{msg_id}:{max_id}")
                    )
                    markup.add(InlineKeyboardButton("✅ Tugadi", callback_data="end"))

                bot.forward_message(call.message.chat.id, channel_id, msg_id)
                bot.send_message(call.message.chat.id,
                    f"📺 {msg_id}/{max_id}-qism",
                    reply_markup=markup)
                found = True
                break
            except:
                next_id += 1
                continue

        if not found:
            bot.answer_callback_query(call.id, "❌ Keyingi topilmadi!")
            return

    elif action == "anime_prev":
        prev_id = current_id - 1
        found = False
        for msg_id in range(prev_id, 0, -1):
            try:
                markup = InlineKeyboardMarkup()
                if msg_id > 1:
                    markup.add(
                        InlineKeyboardButton("⬅️ Oldingi", callback_data=f"anime_prev:{channel_id}:{msg_id}:{max_id}"),
                        InlineKeyboardButton("Keyingisi ➡️", callback_data=f"anime_next:{channel_id}:{msg_id}:{max_id}")
                    )
                else:
                    markup.add(
                        InlineKeyboardButton("Keyingisi ➡️", callback_data=f"anime_next:{channel_id}:{msg_id}:{max_id}")
                    )

                bot.forward_message(call.message.chat.id, channel_id, msg_id)
                bot.send_message(call.message.chat.id,
                    f"📺 {msg_id}/{max_id}-qism",
                    reply_markup=markup)
                found = True
                break
            except:
                prev_id -= 1
                continue

        if not found:
            bot.answer_callback_query(call.id, "❌ Oldingi topilmadi!")
            return

    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "end")
def end_callback(call):
    bot.answer_callback_query(call.id, "✅ Barcha qismlar tugadi!")

# ==================== START ====================

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id,
        "👋 Salom! Anime kodini yuboring 👇\n\n"
        "Kod — kanal postining oxiridagi raqam")

# ==================== ADMIN: MAJBURIY KANALLAR ====================

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
        save_json("channels.json", required_channels)
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
        save_json("channels.json", required_channels)
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
            try:
                chat = bot.get_chat(ch)
                text += f"• {chat.title} ({ch})\n"
            except:
                text += f"• {ch}\n"
        bot.send_message(message.chat.id, text)

# ==================== ADMIN: VIEW KANALLAR ====================

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
    save_json("view.json", view_channels)
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
        save_json("view.json", view_channels)
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
            text += f"• Kod: <b>{code}</b> → {link}\n"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== ADMIN: ANIME KANALLAR (YANGI) ====================

@bot.message_handler(commands=['addanime'])
def add_anime(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id,
            "Format: /addanime [kod] [kanal_id yoki @username]\n"
            "Misol: /addanime 7 -1001234567890\n"
            "Yoki: /addanime 7 @animechannel")
        return
    code = parts[1]
    channel = parts[2]
    try:
        if channel.startswith("@"):
            chat = bot.get_chat(channel)
            channel_id = chat.id
        else:
            channel_id = int(channel)
        anime_channels[code] = channel_id
        save_json("anime_channels.json", anime_channels)
        bot.send_message(message.chat.id, f"✅ Anime kanal qo'shildi!\nKod: <b>{code}</b>\nKanal ID: <code>{channel_id}</code>", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato: {e}")

@bot.message_handler(commands=['removeanime'])
def remove_anime(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /removeanime [kod]\nMisol: /removeanime 7")
        return
    code = parts[1]
    if code in anime_channels:
        del anime_channels[code]
        save_json("anime_channels.json", anime_channels)
        bot.send_message(message.chat.id, f"✅ Anime kanal o'chirildi! Kod: {code}")
    else:
        bot.send_message(message.chat.id, "❌ Bu kod topilmadi!")

@bot.message_handler(commands=['listanime'])
def list_anime(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not anime_channels:
        bot.send_message(message.chat.id, "Hozircha anime kanal yo'q")
    else:
        text = "📋 Anime kanallar:\n\n"
        for code, ch_id in anime_channels.items():
            try:
                chat = bot.get_chat(ch_id)
                text += f"🎬 Kod: <b>{code}</b>\n   Kanal: {chat.title}\n   ID: <code>{ch_id}</code>\n\n"
            except:
                text += f"🎬 Kod: <b>{code}</b> → <code>{ch_id}</code>\n\n"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== ADMIN: STATISTIKA ====================

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    total = len(users)
    banned = len(banned_users)
    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
        f"🚫 Banlanganlar: <b>{banned}</b>\n"
        f"✅ Faol foydalanuvchilar: <b>{total - banned}</b>\n"
        f"📢 Majburiy kanallar: <b>{len(required_channels)}</b>\n"
        f"🎬 Anime kanallar: <b>{len(anime_channels)}</b>\n"
        f"👁 Ko'rish kanallari: <b>{len(view_channels)}</b>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== ADMIN: BROADCAST ====================

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /broadcast [xabar matni]")
        return
    text = parts[1]
    success = 0
    fail = 0
    for uid in users:
        if int(uid) in banned_users:
            continue
        try:
            bot.send_message(int(uid), f"📢 <b>Xabar:</b>\n\n{text}", parse_mode="HTML")
            success += 1
        except:
            fail += 1
    bot.send_message(message.chat.id,
        f"✅ Xabar yuborildi!\n👍 Muvaffaqiyatli: {success}\n❌ Xato: {fail}")

# ==================== ADMIN: BAN / UNBAN ====================

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /ban [user_id]")
        return
    uid = int(parts[1])
    if uid not in banned_users:
        banned_users.append(uid)
        save_json("banned.json", banned_users)
        bot.send_message(message.chat.id, f"🚫 Foydalanuvchi banlandi! ID: {uid}")
    else:
        bot.send_message(message.chat.id, "Bu foydalanuvchi allaqachon banlangan!")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /unban [user_id]")
        return
    uid = int(parts[1])
    if uid in banned_users:
        banned_users.remove(uid)
        save_json("banned.json", banned_users)
        bot.send_message(message.chat.id, f"✅ Foydalanuvchi unbanlandi! ID: {uid}")
    else:
        bot.send_message(message.chat.id, "Bu foydalanuvchi banlangan emas!")

# ==================== ADMIN: YORDAM ====================

@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = (
        "🛠 <b>Admin buyruqlari:</b>\n\n"
        "<b>📢 Majburiy kanallar:</b>\n"
        "/addchannel [id] — kanal qo'shish\n"
        "/removechannel [id] — kanal o'chirish\n"
        "/listchannels — kanallar ro'yxati\n\n"
        "<b>👁 Ko'rish kanallari:</b>\n"
        "/addview [kod] [link] — qo'shish\n"
        "/removeview [kod] — o'chirish\n"
        "/listview — ro'yxat\n\n"
        "<b>🎬 Anime kanallar:</b>\n"
        "/addanime [kod] [kanal_id] — qo'shish\n"
        "/removeanime [kod] — o'chirish\n"
        "/listanime — ro'yxat\n\n"
        "<b>👥 Foydalanuvchilar:</b>\n"
        "/stats — statistika\n"
        "/broadcast [matn] — hammaga xabar\n"
        "/ban [id] — banlash\n"
        "/unban [id] — unbanlash"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ==================== ASOSIY HANDLER ====================

@bot.message_handler(func=lambda m: True)
def handle_code(message):
    user_id = message.from_user.id

    # Ban tekshirish
    if user_id in banned_users:
        bot.send_message(message.chat.id, "🚫 Siz botdan foydalana olmaysiz!")
        return

    # Foydalanuvchini ro'yxatga olish
    register_user(message.from_user)

    # Obuna tekshirish
    not_sub = check_subscription(user_id)
    if not_sub:
        bot.send_message(message.chat.id,
            "⚠️ Botdan foydalanish uchun kanallarga obuna bo'ling!",
            reply_markup=sub_keyboard(not_sub))
        return

    code = message.text.strip()

    # 1. View kanal tekshirish
    if code in view_channels:
        link = view_channels[code]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("👁 Ko'rish", url=link))
        bot.send_message(message.chat.id, "👇 Ko'rish uchun bosing:", reply_markup=markup)
        return

    # 2. Anime kanal tekshirish (sahifalab)
    if code in anime_channels:
        channel_id = anime_channels[code]
        # 1-postdan boshlaymiz
        sent = False
        for msg_id in range(1, 10000):
            try:
                # Kanalda nechta post borligini bilish uchun
                # max_id ni topamiz - oxirgi mavjud postni qidiramiz
                break
            except:
                continue

        # Birinchi mavjud postni topamiz
        first_id = None
        max_id = None

        # Oxirgi postni topish
        for msg_id in range(9999, 0, -1):
            try:
                bot.forward_message(message.chat.id, channel_id, msg_id)
                max_id = msg_id
                break
            except:
                continue

        if max_id is None:
            bot.send_message(message.chat.id, "❌ Kanalda post topilmadi!")
            return

        # Birinchi postni topish
        for msg_id in range(1, max_id + 1):
            try:
                # Birinchi postni foydalanuvchiga yuborish
                bot.forward_message(message.chat.id, channel_id, msg_id)
                first_id = msg_id

                markup = InlineKeyboardMarkup()
                if first_id < max_id:
                    markup.add(InlineKeyboardButton("Keyingisi ➡️", callback_data=f"anime_next:{channel_id}:{first_id}:{max_id}"))
                else:
                    markup.add(InlineKeyboardButton("✅ Tugadi", callback_data="end"))

                bot.send_message(message.chat.id,
                    f"📺 {first_id}/{max_id}-qism",
                    reply_markup=markup)
                sent = True
                break
            except:
                continue

        if not sent:
            bot.send_message(message.chat.id, "❌ Kanal postlari topilmadi!")
        return

    # 3. Asosiy ANIME_CHANNEL dan forward
    try:
        post_id = int(code)
        bot.forward_message(message.chat.id, ANIME_CHANNEL, post_id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Faqat raqam yuboring!")
    except Exception:
        bot.send_message(message.chat.id, "❌ Bunday kod topilmadi!")


bot.polling()
