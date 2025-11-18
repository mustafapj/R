import telebot
import requests
import random
import string
import time
import logging
from threading import Thread, Lock

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"

# إعداد SOCKS لـ Tor
import socket
import socks
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket

bot = telebot.TeleBot(TOKEN)

class UsernameChecker:
    def __init__(self):
        self.available_users = []
        self.checked_count = 0
        self.is_checking = False
        self.lock = Lock()
        
    def generate_username(self, length=5):
        """إنشاء يوزر خماسي عشوائي"""
        characters = string.ascii_lowercase + string.digits + "._"
        return ''.join(random.choice(characters) for _ in range(length))
    
    def check_username_availability(self, username):
        """فحص توفر اليوزر"""
        url = f"https://t.me/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                if "If you have Telegram" in response.text or "tgme_username_error" in response.text:
                    return True  # متاح
                elif "tgme_username" in response.text:
                    return False  # مُستخدم
                    
        except Exception as e:
            logger.error(f"خطأ في فحص @{username}: {e}")
            return None
            
        return False
    
    def start_checking(self, chat_id, count=100):
        """بدء فحص اليوزرات"""
        if self.is_checking:
            bot.send_message(chat_id, "⏳ جاري فحص يوزرات بالفعل...")
            return
            
        self.is_checking = True
        self.available_users = []
        self.checked_count = 0
        
        def check_thread():
            try:
                # إرسال رسالة البدء
                start_msg = f"🔍 **بدأ فحص {count} يوزر خماسي**\n\n⏳ جاري البدء..."
                bot.send_message(chat_id, start_msg, parse_mode='Markdown')
                time.sleep(2)
                
                for i in range(count):
                    if not self.is_checking:
                        break
                        
                    username = self.generate_username()
                    result = self.check_username_availability(username)
                    
                    with self.lock:
                        self.checked_count += 1
                        
                        if result is True:
                            self.available_users.append(username)
                            # إرسال فوري لليوزر المتاح
                            bot.send_message(chat_id, f"🎯 **يوزر متاح:** @{username}", parse_mode='Markdown')
                            logger.info(f"✅ متاح: @{username}")
                        
                        # تحديث الحالة كل 20 يوزر
                        if self.checked_count % 20 == 0:
                            progress = f"📊 **التقدم:** {self.checked_count}/{count}\n✅ **المتاحة:** {len(self.available_users)}"
                            bot.send_message(chat_id, progress, parse_mode='Markdown')
                    
                    # تأخير لتجنب الحظر
                    time.sleep(0.5)
                
                # إرسال النتائج النهائية
                self.send_final_results(chat_id, count)
                
            except Exception as e:
                bot.send_message(chat_id, f"❌ **حدث خطأ:** {e}")
                logger.error(f"خطأ في الفحص: {e}")
            finally:
                self.is_checking = False
        
        # تشغيل الفحص في thread منفصل
        thread = Thread(target=check_thread)
        thread.daemon = True
        thread.start()
    
    def send_final_results(self, chat_id, total_count):
        """إرسال النتائج النهائية"""
        if not self.available_users:
            result_msg = f"""
❌ **انتهى الفحص**

📊 **النتائج:**
• تم فحص: {self.checked_count} يوزر
• المتاحة: 0
• النسبة: 0%

⚠️ **لم يتم العثور على يوزرات متاحة**
"""
        else:
            result_msg = f"""
🎉 **انتهى الفحص بنجاح!**

📊 **النتائج:**
• تم فحص: {self.checked_count} يوزر
• المتاحة: {len(self.available_users)}
• النسبة: {len(self.available_users)/self.checked_count*100:.1f}%

🎯 **اليوزرات المتاحة:**
"""
            for user in self.available_users:
                result_msg += f"• @{user}\n"
        
        bot.send_message(chat_id, result_msg, parse_mode='Markdown')
    
    def stop_checking(self):
        """إيقاف الفحص"""
        self.is_checking = False
        return True

# كائن الفاحص
checker = UsernameChecker()

@bot.message_handler(commands=['start'])
def start(message):
    """رسالة الترحيب"""
    welcome_msg = """
🚀 **بوت فحص اليوزرات الخماسية**

📝 **الأوامر المتاحة:**
/scan100 - فحص 100 يوزر
/scan200 - فحص 200 يوزر  
/scan500 - فحص 500 يوزر
/scan - فحص عدد مخصص
/stop - إيقاف الفحص
/status - حالة البوت

⚡ **المميزات:**
• فحص يوزرات خماسية عشوائية
• إشعار فوري باليوزرات المتاحة
• إحصائيات مفصلة
• حماية من الحظر عبر Tor
"""
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')

@bot.message_handler(commands=['scan100'])
def scan_100(message):
    """فحص 100 يوزر"""
    checker.start_checking(message.chat.id, 100)

@bot.message_handler(commands=['scan200'])
def scan_200(message):
    """فحص 200 يوزر"""
    checker.start_checking(message.chat.id, 200)

@bot.message_handler(commands=['scan500'])
def scan_500(message):
    """فحص 500 يوزر"""
    checker.start_checking(message.chat.id, 500)

@bot.message_handler(commands=['scan'])
def scan_custom(message):
    """فحص عدد مخصص"""
    msg = bot.reply_to(message, "🔢 **كم يوزر تريد فحصه؟**\n\nأدخل رقم بين 10 و 1000:")
    bot.register_next_step_handler(msg, process_custom_scan)

def process_custom_scan(message):
    """معالجة العدد المخصص"""
    try:
        count = int(message.text)
        if count < 10 or count > 1000:
            bot.reply_to(message, "❌ **الرجاء إدخال رقم بين 10 و 1000**")
            return
        
        bot.reply_to(message, f"🔍 **بدأ فحص {count} يوزر...**")
        checker.start_checking(message.chat.id, count)
        
    except ValueError:
        bot.reply_to(message, "❌ **الرجاء إدخال رقم صحيح**")

@bot.message_handler(commands=['stop'])
def stop_scan(message):
    """إيقاف الفحص"""
    if checker.stop_checking():
        bot.reply_to(message, "⏹️ **تم إيقاف الفحص**")
    else:
        bot.reply_to(message, "ℹ️ **لا يوجد فحص نشط**")

@bot.message_handler(commands=['status'])
def status(message):
    """حالة البوت"""
    status_msg = f"""
🟢 **حالة البوت:**

• البوت: نشط ✅
• Tor: متصل ✅  
• الفحص النشط: {'نعم' if checker.is_checking else 'لا'}
• تم فحص: {checker.checked_count} يوزر
• اليوزرات المتاحة: {len(checker.available_users)}
"""
    bot.send_message(message.chat.id, status_msg, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """رد على الرسائل الأخرى"""
    bot.reply_to(message, "❓ **استخدم /start لرؤية الأوامر**")

if __name__ == "__main__":
    logger.info("بدأ تشغيل بوت فحص اليوزرات...")
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")