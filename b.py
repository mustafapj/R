import telebot
import requests
import random
import string
import time
import logging
from threading import Thread, Lock
from queue import Queue

# ===== إعداد التسجيل =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TOKEN = "ضع_توكن_البوت_هنا"

bot = telebot.TeleBot(TOKEN)

# ===== إعدادات قابلة للتخصيص =====
MAX_CHECKS = 500  # الحد الأقصى للفحوصات
DELAY_BETWEEN_CHECKS = 0.5  # تأخير بين الفحوصات (بالثواني)
BATCH_SIZE = 10  # عدد اليوزرات في كل رسالة

class UsernameChecker:
    def __init__(self):
        self.available_users = []
        self.lock = Lock()
        self.checked_count = 0
        
    def generate_username(self, length=5):
        """إنشاء يوزر عشوائي مع تحسين التنوع"""
        characters = string.ascii_lowercase + string.digits + "._"
        
        # تحسين التنوع في اليوزرات
        patterns = [
            lambda: ''.join(random.choice(characters) for _ in range(length)),
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(length)),
            lambda: ''.join(random.choice(string.ascii_lowercase) for i in range(length)) + random.choice(string.digits),
        ]
        
        return random.choice(patterns)()
    
    def check_username_availability(self, username):
        """فحص توفر اليوزر مع معالجة أفضل للأخطاء"""
        url = f"https://t.me/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # فحص أكثر دقة للتوفّر
            if response.status_code == 200:
                if "If you have Telegram" in response.text or "tgme_username_error" in response.text:
                    return True  # اليوزر متاح
                elif "tgme_username" in response.text:
                    return False  # اليوزر مُستخدم
                    
        except requests.exceptions.RequestException as e:
            logger.warning(f"خطأ في فحص @{username}: {e}")
            return None  # خطأ في الاتصال
            
        return False
    
    def check_batch(self, chat_id, num_checks):
        """فحص مجموعة من اليوزرات"""
        self.available_users = []
        self.checked_count = 0
        
        start_time = time.time()
        
        for i in range(num_checks):
            username = self.generate_username()
            result = self.check_username_availability(username)
            
            with self.lock:
                self.checked_count += 1
                
                if result is True:
                    self.available_users.append(username)
                    logger.info(f"✅ متاح: @{username}")
                    
                    # إرسال اليوزرات المتاحة فوراً
                    if len(self.available_users) >= 1:
                        try:
                            bot.send_message(chat_id, f"✨ متاح: @{username}")
                            self.available_users = []
                        except Exception as e:
                            logger.error(f"خطأ في إرسال الرسالة: {e}")
                
                elif result is None:
                    logger.warning(f"⏸️  خطأ اتصال: @{username}")
                
                # تحديث الحالة كل 50 فحص
                if self.checked_count % 50 == 0:
                    progress = f"📊 تم فحص {self.checked_count}/{num_checks} - المتاحة: {len(self.available_users)}"
                    try:
                        bot.send_message(chat_id, progress)
                    except:
                        pass
            
            # تأخير لتجنب الحظر
            time.sleep(DELAY_BETWEEN_CHECKS)
        
        # إرسال النتائج النهائية
        end_time = time.time()
        duration = end_time - start_time
        
        summary = f"""
✅ **انتهى الفحص!**

📊 **النتائج:**
• تم فحص: {self.checked_count} يوزر
• اليوزرات المتاحة: {len(self.available_users)}
• المدة: {duration:.2f} ثانية
• السرعة: {self.checked_count/duration:.2f} يوزر/ثانية

🎯 **اليوزرات المتاحة:**
"""
        if self.available_users:
            for user in self.available_users:
                summary += f"• @{user}\n"
        else:
            summary += "❌ لم يتم العثور على يوزرات متاحة"
        
        try:
            bot.send_message(chat_id, summary, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"خطأ في إرسال النتائج: {e}")

# كائن فاحص اليوزرات
checker = UsernameChecker()

@bot.message_handler(commands=['start'])
def start_command(message):
    """رسالة الترحيب"""
    welcome_text = """
🚀 **بوت فحص اليوزرات الخماسية**

📝 **الأوامر المتاحة:**
/check - فحص 500 يوزر عشوائي
/check200 - فحص 200 يوزر
/check1000 - فحص 1000 يوزر
/custom - فحص عدد مخصص

⚡ **مميزات البوت:**
• فحص سريع ودقيق
• إشعار فوري باليوزرات المتاحة
• إحصائيات مفصلة
• حماية من الحظر
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['check'])
def check_500(message):
    """فحص 500 يوزر"""
    bot.reply_to(message, "🔥 بدأ فحص 500 يوزر خماسي...")
    
    # تشغيل الفحص في thread منفصل
    thread = Thread(target=checker.check_batch, args=(message.chat.id, 500))
    thread.daemon = True
    thread.start()

@bot.message_handler(commands=['check200'])
def check_200(message):
    """فحص 200 يوزر"""
    bot.reply_to(message, "🔥 بدأ فحص 200 يوزر خماسي...")
    
    thread = Thread(target=checker.check_batch, args=(message.chat.id, 200))
    thread.daemon = True
    thread.start()

@bot.message_handler(commands=['check1000'])
def check_1000(message):
    """فحص 1000 يوزر"""
    bot.reply_to(message, "🔥 بدأ فحص 1000 يوزر خماسي...")
    
    thread = Thread(target=checker.check_batch, args=(message.chat.id, 1000))
    thread.daemon = True
    thread.start()

@bot.message_handler(commands=['custom'])
def custom_check(message):
    """فحص عدد مخصص"""
    msg = bot.reply_to(message, "🔢 الرجاء إدخال عدد اليوزرات التي تريد فحصها (1-5000):")
    bot.register_next_step_handler(msg, process_custom_amount)

def process_custom_amount(message):
    """معالجة العدد المخصص"""
    try:
        amount = int(message.text)
        if amount < 1 or amount > 5000:
            bot.reply_to(message, "❌ الرجاء إدخال عدد بين 1 و 5000")
            return
            
        bot.reply_to(message, f"🔥 بدأ فحص {amount} يوزر خماسي...")
        
        thread = Thread(target=checker.check_batch, args=(message.chat.id, amount))
        thread.daemon = True
        thread.start()
        
    except ValueError:
        bot.reply_to(message, "❌ الرجاء إدخال رقم صحيح")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض إحصائيات"""
    stats_text = """
📊 **إحصائيات البوت:**

• الفحص يعمل بدون بروكسي
• دقة فحص عالية
• سرعة متوسطة: 2 يوزر/ثانية
• تأخير بين الطلبات: 0.5 ثانية
    """
    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """رد على أي رسالة أخرى"""
    bot.reply_to(message, "❓ استخدم /start لرؤية الأوامر المتاحة")

if __name__ == "__main__":
    logger.info("بدأ تشغيل البوت...")
    try:
        bot.infinity_polling(timeout=60, skip_pending=True)
    except Exception as e:
        logger.error(f"خطأ في تشغيل البوت: {e}")