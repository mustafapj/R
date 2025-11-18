import telebot
import requests
import time

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"

# إعدادات Tor
proxies = {
    'https': 'socks5h://127.0.0.1:9050',
    'http': 'socks5h://127.0.0.1:9050'
}

# تطبيق البروكسي على telebot
telebot.apihelper.proxy = proxies

bot = telebot.TeleBot(TOKEN)

# تخزين chat_id للإشعارات
admin_chat_id = None

@bot.message_handler(commands=['start'])
def start(message):
    global admin_chat_id
    admin_chat_id = message.chat.id
    
    # إرسال إشعار بدء العمل
    bot.send_message(admin_chat_id, "🔧 **جاري بدء التشغيل عبر Tor...**")
    
    time.sleep(2)
    bot.reply_to(message, "✅ **تم بدء التشغيل بنجاح!**\n\nاستخدم /test لفحص الاتصال")

@bot.message_handler(commands=['test'])
def test(message):
    try:
        bot.send_message(message.chat.id, "🔍 **جاري فحص الاتصال بـ Telegram...**")
        time.sleep(1)
        
        # اختبار الاتصال عبر Tor
        response = requests.get("https://api.telegram.org", proxies=proxies, timeout=10)
        bot.send_message(message.chat.id, f"✅ **الاتصال ناجح!**\n\nالرمز: {response.status_code}")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ **فشل الاتصال:**\n{e}")

@bot.message_handler(commands=['check'])
def check_tor(message):
    try:
        bot.send_message(message.chat.id, "🕵️ **جاري فحص إعدادات Tor...**")
        time.sleep(1)
        
        # اختبار عنوان IP عبر Tor
        response = requests.get("https://check.torproject.org/", proxies=proxies, timeout=10)
        if "Congratulations" in response.text:
            bot.send_message(message.chat.id, "🎉 **Tor يعمل بشكل ممتاز!**\n\nأنت متصل بشكل آمن ومخفي")
        else:
            bot.send_message(message.chat.id, "⚠️ **Tor يعمل ولكن هناك مشكلة في الإخفاء**")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ **فشل فحص Tor:**\n{e}")

@bot.message_handler(commands=['status'])
def status(message):
    bot.send_message(message.chat.id, "🟢 **البوت يعمل بشكل طبيعي**\n\n✅ متصل عبر Tor\n✅ جاهز لاستقبال الأوامر")

def send_startup_notification():
    """إرسال إشعار عند بدء تشغيل البوت"""
    global admin_chat_id
    if admin_chat_id:
        try:
            bot.send_message(admin_chat_id, "🚀 **تم تشغيل البوت بنجاح!**\n\nاكتب /start لبدء الاستخدام")
        except:
            pass

print("🔄 جاري تشغيل البوت عبر Tor...")
try:
    # بدء البوت
    bot.polling(none_stop=True, timeout=60)
    
except Exception as e:
    print(f"❌ خطأ: {e}")
    
    # إرسال إشعار خطأ إذا كان admin_chat_id معروف
    if admin_chat_id:
        try:
            bot.send_message(admin_chat_id, f"❌ **توقف البوت بسبب خطأ:**\n{e}")
        except:
            pass