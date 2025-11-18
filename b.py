import telebot
import requests
import time

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ البوت يعمل! الاتصال ناجح.")

@bot.message_handler(commands=['test'])
def test(message):
    try:
        # اختبار الاتصال
        response = requests.get("https://api.telegram.org", timeout=10)
        bot.reply_to(message, f"✅ الاتصال ناجح - Status: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"❌ فشل الاتصال: {e}")

print("جاري تشغيل البوت...")
try:
    bot.polling(none_stop=True, timeout=60)
except Exception as e:
    print(f"خطأ: {e}")