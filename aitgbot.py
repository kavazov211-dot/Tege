import os
import re
import asyncio
import time
from telebot import telebot, types
from telebot.apihelper import ApiTelegramException
import edge_tts

TOKEN = "8435803353:AAEp9z8amY-M69uOk76DKS0ztd1Y-YozFN0"
bot = telebot.TeleBot(TOKEN)

user_settings = {}
FLOOD_DELAY = 3

VOICES = {
    "uz": {"female": "uz-UZ-MadinaNeural", "male": "uz-UZ-SardorNeural"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural"}
}

def get_user_data(chat_id):
    if chat_id not in user_settings:
        user_settings[chat_id] = {
            "lang": None,  # 🔥 Boshida til tanlanmagan (None) bo'ladi
            "voice": "female",
            "speed": "normal",
            "last_time": 0
        }
    return user_settings[chat_id]

# --- KEYBOARDS ---
def main_menu_keyboard(chat_id):
    data = get_user_data(chat_id)
    lang = data["lang"] if data["lang"] else "uz"  
    txt = {"uz": ["🎤 Ovoz sozlamalari", "🌐 Tilni almashtirish"], "ru": ["🎤 Настройки голоса", "🌐 Сменить язык"]}[lang]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(txt[0], callback_data="menu_voice"), types.InlineKeyboardButton(txt[1], callback_data="menu_lang"))
    return markup

def voice_settings_keyboard(chat_id):
    data = get_user_data(chat_id)
    lang = data["lang"] if data["lang"] else "uz"
    v, s = data["voice"], data["speed"]
    f_check = "✅ " if v == "female" else ""
    m_check = "✅ " if v == "male" else ""
    s_slow = "✅ " if s == "slow" else ""
    s_norm = "✅ " if s == "normal" else ""
    s_fast = "✅ " if s == "fast" else ""
    
    labels = {
        "uz": ["👩 Ayol", "👨 Erkak", "👑 Studio Effektlar (Premium)", "🐢 Sekin", "🚶 Norm", "⚡ Tez", "🔙 Orqaga"],
        "ru": ["👩 Женский", "👨 Мужской", "👑 Студийные Эффекты (Прем)", "🐢 Медленно", "🚶 Норм", "⚡ Быстро", "Назад"]
    }[lang]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton(f"{f_check}{labels[0]}", callback_data="set_v_female"), types.InlineKeyboardButton(f"{m_check}{labels[1]}", callback_data="set_v_male"))
    markup.add(types.InlineKeyboardButton(labels[2], callback_data="menu_premium"), row_width=1)
    markup.add(types.InlineKeyboardButton(f"{s_slow}{labels[3]}", callback_data="set_s_slow"), types.InlineKeyboardButton(f"{s_norm}{labels[4]}", callback_data="set_s_normal"), types.InlineKeyboardButton(f"{s_fast}{labels[5]}", callback_data="set_s_fast"))
    markup.add(types.InlineKeyboardButton(labels[6], callback_data="main_menu"), row_width=1)
    return markup

def premium_effects_keyboard(chat_id):
    data = get_user_data(chat_id)
    lang = data["lang"] if data["lang"] else "uz"
    v = data["voice"]
    
    r_check = "✅ " if v == "robot" else ""
    mon_check = "✅ " if v == "monster" else ""
    baby_check = "✅ " if v == "baby" else ""
    mouse_check = "✅ " if v == "mouse" else ""
    
    labels = {
        "uz": ["🤖 Kiber-Robot", "👹 Vahshiy Maxluq", "👶 'Bola ovozi", "🐭 Mitti Sichqoncha", "🔙 Orqaga"],
        "ru": ["🤖 Кибер-Робот", "👹 Дикий Монстр", "👶 Детский голос", "🐭 Мышонок", "🔙 Назад"]
    }[lang]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"{r_check}{labels[0]}", callback_data="set_v_robot"), 
        types.InlineKeyboardButton(f"{mon_check}{labels[1]}", callback_data="set_v_monster"),
        types.InlineKeyboardButton(f"{baby_check}{labels[2]}", callback_data="set_v_baby"),
        types.InlineKeyboardButton(f"{mouse_check}{labels[3]}", callback_data="set_v_mouse"),
        types.InlineKeyboardButton(labels[4], callback_data="menu_voice")
    )
    return markup

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    get_user_data(chat_id)
    
    try:
        bot.send_message(chat_id, "👋")
    except Exception as e:
        print(f"Emoji send error: {e}")
        
    markup = types.InlineKeyboardMarkup()  
    markup.add(
        types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"), 
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    )  
    
    sent_msg = bot.send_message(chat_id, "Tilni tanlang / Выберите язык 👇", reply_markup=markup)
    
    try:
        bot.pin_chat_message(chat_id, sent_msg.message_id, disable_notification=True)
    except Exception as e:
        print(f"Pin error: {e}")

# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id  
    data = get_user_data(chat_id)
    try:
        if call.data.startswith("lang_"):
            data["lang"] = call.data.split("_")[1]
            msg_text = "✅ Matn yuboring 🎤" if data["lang"] == "uz" else "✅ Отправьте текст 🎤"
            bot.edit_message_text(msg_text, chat_id, call.message.message_id, reply_markup=main_menu_keyboard(chat_id))
        elif call.data == "main_menu":
            bot.edit_message_text("Asosiy menyu:", chat_id, call.message.message_id, reply_markup=main_menu_keyboard(chat_id))
        elif call.data == "menu_voice":
            bot.edit_message_text("Ovozni sozlang:", chat_id, call.message.message_id, reply_markup=voice_settings_keyboard(chat_id))
        elif call.data == "menu_premium":
            bot.edit_message_text("✨ Studiyaviy kuchli effektlar:", chat_id, call.message.message_id, reply_markup=premium_effects_keyboard(chat_id))
        elif call.data == "menu_lang":
            markup = types.InlineKeyboardMarkup()  
            markup.add(
                types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz"), 
                types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
            )  
            bot.edit_message_text("Tilni tanlang / Выберите язык 👇", chat_id, call.message.message_id, reply_markup=markup)
            
        elif call.data.startswith("set_v_"):
            data["voice"] = call.data.replace("set_v_", "")
            if data["voice"] in ["robot", "monster", "baby", "mouse"]:
                bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=premium_effects_keyboard(chat_id))
            else:
                bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=voice_settings_keyboard(chat_id))
        elif call.data.startswith("set_s_"):
            data["speed"] = call.data.replace("set_s_", "")
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=voice_settings_keyboard(chat_id))
    except ApiTelegramException as e:
        if "message is not modified" not in e.description:
            print(f"Telegram API Error: {e}")

# --- MATNNI OVOZGA AYLANTIRISH TIZIMI ---
@bot.message_handler(func=lambda m: True)
def voice_generation(message):
    chat_id = message.chat.id
    
    if chat_id not in user_settings or user_settings[chat_id]["lang"] is None:
        return

    data = user_settings[chat_id]
    
    if message.text and message.text.startswith('/start'):
        return

    if not message.text or str(message.text).isspace():
        return

    current_time = time.time()
    if current_time - data["last_time"] < FLOOD_DELAY:
        bot.send_message(chat_id, "⚠️ Iltimos biroz kuting!")
        return
    
    text = message.text.lower()  
    clean_text = "".join(c for c in text if c.isalnum())  
    if re.search(r"k.*m.*r.*n", clean_text) or re.search(r"a.*v.*z.*v", clean_text):
        bot.send_message(chat_id, "❌ Taqiqlangan so'z!")  
        return  

    data["last_time"] = current_time
    v_type = data["voice"]
    
    # Premium ovozlar uchun ham mos asosiy til tanlanadi
    if v_type in ["robot", "monster", "baby", "mouse"]:
        voice_name = VOICES[data["lang"]]["male"] if v_type == "monster" else VOICES[data["lang"]]["female"]
    else:
        voice_name = VOICES[data["lang"]].get(v_type, VOICES[data["lang"]]["female"])

    pitch_val = "+0Hz"
    speed_map = {"slow": "-25%", "normal": "+0%", "fast": "+25%"}
    rate_val = speed_map.get(data["speed"], "+0%")

    # 🔥 PREMIUM EFFEKTLARNING CHASTOTA SOZLAMALARI:
    if v_type == "robot":
        pitch_val = "+50Hz"   
        rate_val = "+20%"     
    elif v_type == "monster":
        pitch_val = "-30Hz"   
        rate_val = "-12%"     
    elif v_type == "baby":
        pitch_val = "+35Hz"   # Bolakay ovozi effekti
        rate_val = "+5%"
    elif v_type == "mouse":
        pitch_val = "+90Hz"   # Ingichka sichqoncha ovozi effekti
        rate_val = "+22%"     

    filename = f"voice_{chat_id}.mp3"
    status_msg = bot.send_message(chat_id, "⏳ Ovoz yuqori sifatda yaratilmoqda...")

    async def generate():  
        communicate = edge_tts.Communicate(message.text, voice_name, rate=rate_val, pitch=pitch_val)
        await communicate.save(filename)

    success = False
    for attempt in range(3):
        try:
            asyncio.run(generate())  
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                success = True
                break
        except Exception as e:
            print(f"Urinish xatosi: {e}")
            time.sleep(1)

    try:
        if success:
            with open(filename, "rb") as audio:  
                bot.send_voice(chat_id, audio, reply_to_message_id=message.message_id)  
        else:
            raise Exception("Fayl topilmadi.")
    except Exception as e:
        bot.send_message(chat_id, "❌ Server bandligi sababli xatolik yuz berdi. Qayta urinib ko'ring.")
        print(f"Xatolik tafsiloti: {e}")
    finally:
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except Exception:
            pass
        if os.path.exists(filename):
            os.remove(filename)

print("Bot muvaffaqiyatli ishga tushdi...")
bot.infinity_polling()
