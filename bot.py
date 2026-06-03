import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8824206791:AAGMJWQMD_mG6Io1VfHtLWaQ04qxKlowsAE"
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
anime_messages = load_json("anime_messages.json", {})  # {kod: {qism: msg_id}}
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("ep:"))
def episode_callback(call):
    # ep:kod:qism
    parts = call.data.split(":")
    kod = parts[1]
    qism = int(parts[2])

    messages = anime_messages.get(kod, {})
    total = len(messages)
    channel_id = anime_channels.get(kod)

    if not channel_id or str(qism) not in messages:
        bot.answer_callback_query(call.id, "❌ Topilmadi!")
        return

    msg_id = messages[str(qism)]

    markup = InlineKeyboardMarkup()
    row = []
    if qism > 1:
        row.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"ep:{kod}:{qism-1}"))
    if qism < total:
        row.append(InlineKeyboardButton("Keyingisi ➡️", callback_data=f"ep:{kod}:{qism+1}"))
    if row:
        markup.add(*row)
    if qism == total:
        markup.add(InlineKeyboardButton("✅ Tugadi", callback_data="end"))

    try:
        bot.copy_message(call.message.chat.id, channel_id, msg_id)
        bot.send_message(call.message.chat.id, f"📺 {qism}/{total}-qism", reply_markup=markup)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Xatolik: {e}")

    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "end")
def end_callback(call):
    bot.answer_callback_query(call.id, "✅ Barcha qismlar tugadi!")

# ==================== KANAL POSTLARINI SAQLASH ====================

@bot.channel_post_handler(func=lambda m: True)
def save_channel_post(message):
    caption = (message.caption or message.text or "").strip()
    if not caption:
        return

    # Format: kod_qism  masalan: 7_1, 7_2
    parts = caption.split("_")
    if len(parts) != 2:
        return

    kod = parts[0].strip()
    try:
        qism = int(parts[1].strip())
    except ValueError:
        return

    if kod not in anime_channels:
        return

    if anime_channels[kod] != message.chat.id:
        return

    if kod not in anime_messages:
        anime_messages[kod] = {}

    anime_messages[kod][str(qism)] = message.message_id
    save_json("anime_messages.json", anime_messages)
    print(f"✅ Saqlandi: kod={kod}, qism={qism}, msg_id={message.message_id}")

# ==================== START ====================

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user)
    bot.send_message(message.chat.id,
        "👋 Salom! Anime kodini yuboring 👇")

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

# ==================== ADMIN: ANIME KANALLAR ====================

@bot.message_handler(commands=['addanime'])
def add_anime(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.send_message(message.chat.id,
            "Format: /addanime [kod] [kanal_id]\n"
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
        bot.send_message(message.chat.id,
            f"✅ Anime kanal qo'shildi!\nKod: <b>{code}</b>\n"
            f"Kanal ID: <code>{channel_id}</code>\n\n"
            f"Endi kanalga video tashlang, caption ga:\n"
            f"<code>{code}_1</code>, <code>{code}_2</code> ... yozing",
            parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato: {e}")

@bot.message_handler(commands=['removeanime'])
def remove_anime(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Format: /removeanime [kod]")
        return
    code = parts[1]
    if code in anime_channels:
        del anime_channels[code]
        save_json("anime_channels.json", anime_channels)
        if code in anime_messages:
            del anime_messages[code]
            save_json("anime_messages.json", anime_messages)
        bot.send_message(message.chat.id, f"✅ O'chirildi! Kod: {code}")
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
            count = len(anime_messages.get(code, {}))
            try:
                chat = bot.get_chat(ch_id)
                text += f"🎬 Kod: <b>{code}</b>\n   Kanal: {chat.title}\n   📹 {count} ta video\n\n"
            except:
                text += f"🎬 Kod: <b>{code}</b> → <code>{ch_id}</code>\n   📹 {count} ta video\n\n"
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
        f"✅ Faol: <b>{total - banned}</b>\n"
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
        f"✅ Yuborildi!\n👍 Muvaffaqiyatli: {success}\n❌ Xato: {fail}")

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
        bot.send_message(message.chat.id, f"🚫 Banlandi! ID: {uid}")
    else:
        bot.send_message(message.chat.id, "Allaqachon banlangan!")

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
        bot.send_message(message.chat.id, f"✅ Unbanlandi! ID: {uid}")
    else:
        bot.send_message(message.chat.id, "Banlangan emas!")

# ==================== ADMIN: YORDAM ====================

@bot.message_handler(commands=['help'])
def help_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = (
        "🛠 <b>Admin buyruqlari:</b>\n\n"
        "<b>📢 Majburiy kanallar:</b>\n"
        "/addchannel [id] — qo'shish\n"
        "/removechannel [id] — o'chirish\n"
        "/listchannels — ro'yxat\n\n"
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

    if user_id in banned_users:
        bot.send_message(message.chat.id, "🚫 Siz botdan foydalana olmaysiz!")
        return

    register_user(message.from_user)

    not_sub = check_subscription(user_id)
    if not_sub:
        bot.send_message(message.chat.id,
            "⚠️ Botdan foydalanish uchun kanallarga obuna bo'ling!",
            reply_markup=sub_keyboard(not_sub))
        return

    code = message.text.strip()

    # 1. View kanal
    if code in view_channels:
        link = view_channels[code]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("👁 Ko'rish", url=link))
        bot.send_message(message.chat.id, "👇 Ko'rish uchun bosing:", reply_markup=markup)
        return

    # 2. Anime kanal (caption usuli)
    if code in anime_channels:
        messages = anime_messages.get(code, {})
        if not messages:
            bot.send_message(message.chat.id,
                "📭 Hali video yo'q.\n"
                f"Kanalga video tashlang, caption ga <code>{code}_1</code> yozing.",
                parse_mode="HTML")
            return

        total = len(messages)
        channel_id = anime_channels[code]
        msg_id = messages.get("1")

        if not msg_id:
            bot.send_message(message.chat.id, "❌ 1-qism topilmadi!")
            return

        markup = InlineKeyboardMarkup()
        if total > 1:
            markup.add(InlineKeyboardButton("Keyingisi ➡️", callback_data=f"ep:{code}:2"))
        else:
            markup.add(InlineKeyboardButton("✅ Tugadi", callback_data="end"))

        try:
            bot.copy_message(message.chat.id, channel_id, msg_id)
            bot.send_message(message.chat.id, f"📺 1/{total}-qism", reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Xatolik: {e}")
        return

    # 3. Asosiy ANIME_CHANNEL
    try:
        post_id = int(code)
        bot.forward_message(message.chat.id, ANIME_CHANNEL, post_id)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Faqat raqam yuboring!")
    except Exception:
        bot.send_message(message.chat.id, "❌ Bunday kod topilmadi!")


bot.polling(allowed_updates=["message", "callback_query", "channel_post"])
