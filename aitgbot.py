import telebot
from telebot import types
import edge_tts
import asyncio
import os

TOKEN = "7585451169:AAF5kBJjD2HjMzcEXTztr5UmCxRtvxqaT2Y"

bot = telebot.TeleBot(TOKEN)

user_lang = {}

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.InlineKeyboardMarkup()

    uz_btn = types.InlineKeyboardButton(
        "🇺🇿 O'zbekcha",
        callback_data="uz"
    )

    ru_btn = types.InlineKeyboardButton(
        "🇷🇺 Русский",
        callback_data="ru"
    )

    markup.add(uz_btn, ru_btn)

    bot.send_message(
        message.chat.id,
        "Tilni tanlang 👇",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    if call.data == "uz":

        user_lang[call.message.chat.id] = "uz"

        bot.edit_message_text(
            "✅ O'zbekcha tanlandi\n\nMatn yuboring 🎤",
            call.message.chat.id,
            call.message.message_id
        )

    elif call.data == "ru":

        user_lang[call.message.chat.id] = "ru"

        bot.edit_message_text(
            "✅ Русский выбран\n\nОтправьте текст 🎤",
            call.message.chat.id,
            call.message.message_id
        )


@bot.message_handler(func=lambda m: True)
def voice(message):

    text = message.text
    filename = "voice.mp3"

    lang = user_lang.get(message.chat.id, "uz")

    if lang == "uz":
        voice_name = "uz-UZ-MadinaNeural"
    else:
        voice_name = "ru-RU-SvetlanaNeural"

    async def generate():
        communicate = edge_tts.Communicate(
            text,
            voice_name,
            rate="-30%"   # 👈 SEKIN GAPIRISH
        )
        await communicate.save(filename)

    asyncio.run(generate())

    with open(filename, "rb") as audio:
        bot.send_voice(message.chat.id, audio)

    os.remove(filename)


print("Bot ishladi...")
bot.infinity_polling()
