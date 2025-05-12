# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types
import telebot
from telebot import types as telebot_types
import time
from dotenv import load_dotenv  # добавил импорт

# Загрузка переменных окружения из .env
load_dotenv()

# Словарь для хранения сессий Gemini по user_id
user_sessions = {}

# Функция для получения или создания сессии Gemini для пользователя
def get_user_chat(user_id):
    if user_id not in user_sessions:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])  # теперь из .env
        model = "gemini-2.5-flash-preview-04-17"
        tools = [types.Tool(google_search=types.GoogleSearch())]
        config = types.GenerateContentConfig(
            tools=tools,
            response_mime_type="text/plain",
        )
        chat = client.chats.create(model=model, config=config)
        user_sessions[user_id] = chat
    return user_sessions[user_id]

# Новая функция генерации ответа с учётом сессии
def generate_gemini_response(user_id, user_text):
    chat = get_user_chat(user_id)
    response = chat.send_message(user_text)
    return response.text

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]  # теперь из .env
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Клавиатура с кнопкой "Новый чат"
keyboard = telebot_types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(telebot_types.KeyboardButton("Новый чат"))

@bot.message_handler(func=lambda message: message.text == "Новый чат")
def new_chat_handler(message):
    user_id = message.from_user.id
    user_sessions.pop(user_id, None)  # Удаляем старую сессию
    bot.send_message(message.chat.id, "Context reset. New chat started!", reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = generate_gemini_response(user_id, user_text)
        bot.send_message(message.chat.id, response, reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}", reply_markup=keyboard)

if __name__ == "__main__":
    print("Bot started!")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(15)  # Подождать перед повтором
