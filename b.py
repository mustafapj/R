import telebot
import requests
import random
import string
import time
import threading
from datetime import datetime

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
bot = telebot.TeleBot(TOKEN)

class UltraFastChecker:
    def __init__(self):
        self.is_checking = False
        self.checked_count = 0
        self.found_count = 0
        self.start_time = None
        self.current_chat_id = None
        self.session = requests.Session()
        
    def generate_username(self):
        """إنشاء يوزر سريع"""
        chars = string.ascii_lowercase + string.digits
        # أنماط مختلفة لزيادة الفرص
        patterns = [
            lambda: ''.join(random.choice(chars) for _ in range(5)),  # خماسي
            lambda: ''.join(random.choice(chars) for _ in range(6)),  # سداسي
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(4)) + random.choice(string.digits),  # 4 أحرف + رقم
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(3)) + ''.join(random.choice(string.digits) for _ in range(2)),  # 3 أحرف + 2 رقم
        ]
        return random.choice(patterns)()
    
    def check_username_ultra_fast(self, username):
        """فحص فائق السرعة"""
        try:
            # استخدام وقت استجابة أقصر
            response = self.session.get(
                f"https://t.me/{username}", 
                timeout=2,  # وقت أقل
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            # فحص سريع
            return "If you have Telegram" in response.text
        except:
            return False
    
    def start_ultra_fast_check(self, chat_id):
        """بدء الفحص فائق السرعة"""
        if self.is_checking:
            bot.send_message(chat_id, "⚡ الفحص يعمل بالفعل!")
            return
        
        self.is_checking = True
        self.checked_count = 0
        self.found_count = 0
        self.start_time = datetime.now()
        self.current_chat_id = chat_id
        
        bot.send_message(chat_id, "🚀 **بدأ الفحص فائق السرعة!**\n⚡ السرعة: ~20 يوزر/ثانية\n🎯 الإرسال فوري لكل يوزر متاح")
        
        def ultra_fast_check():
            batch_size = 5  # فحص 5 يوزرات قبل التأخير
            batch_count = 0
            
            while self.is_checking:
                # فحص مجموعة يوزرات
                for _ in range(batch_size):
                    username = self.generate_username()
                    self.checked_count += 1
                    
                    if self.check_username_ultra_fast(username):
                        self.found_count += 1
                        # إرسال فوري
                        try:
                            bot.send_message(self.current_chat_id, f"🎯 **يوزر متاح:** @{username}")
                        except:
                            pass
                
                batch_count += 1
                
                # إرسال إحصائية كل 10 batches (50 يوزر)
                if batch_count % 10 == 0:
                    self.send_quick_stats()
                
                # تأخير بسيط جداً
                if self.is_checking:
                    time.sleep(0.05)  # 50 مللي ثانية فقط!
        
        # تشغيل الفحص
        self.check_thread = threading.Thread(target=ultra_fast_check)
        self.check_thread.daemon = True
        self.check_thread.start()
    
    def send_quick_stats(self):
        """إرسال إحصائية سريعة"""
        if not self.current_chat_id or self.checked_count == 0:
            return
        
        current_time = datetime.now()
        duration = (current_time - self.start_time).total_seconds()
        speed = self.checked_count / duration if duration > 0 else 0
        
        try:
            if self.checked_count % 500 == 0:  # كل 500 يوزر
                bot.send_message(
                    self.current_chat_id, 
                    f"📊 **تقدم سريع:**\nفحص: {self.checked_count:,} يوزر\nوجد: {self.found_count} يوزر\n⚡ السرعة: {speed:.1f}/ثانية"
                )
        except:
            pass
    
    def stop_check(self, chat_id):
        """إيقاف الفحص"""
        if not self.is_checking:
            bot.send_message(chat_id, "⏸️ لا يوجد فحص نشط")
            return False
        
        self.is_checking = False
        time.sleep(0.2)
        
        # الإحصائيات النهائية
        current_time = datetime.now()
        duration = (current_time - self.start_time).total_seconds()
        speed = self.checked_count / duration if duration > 0 else 0
        
        final_stats = f"""
✅ **انتهى الفحص فائق السرعة!**

📊 **النتائج النهائية:**
• تم فحص: {self.checked_count:,} يوزر
• تم العثور: {self.found_count} يوزر
• النسبة: {(self.found_count/self.checked_count*100) if self.checked_count > 0 else 0:.3f}%
• السرعة: {speed:.1f} يوزر/ثانية
• المدة: {duration:.1f} ثانية
"""
        bot.send_message(chat_id, final_stats)
        return True
    
    def get_status(self):
        """حالة الفحص"""
        if not self.is_checking:
            return "⏸️ متوقف"
        
        duration = (datetime.now() - self.start_time).total_seconds()
        speed = self.checked_count / duration if duration > 0 else 0
        
        return f"⚡ نشط - فحص: {self.checked_count:,} - وجد: {self.found_count} - السرعة: {speed:.1f}/ثانية"

# الكائن الرئيسي
checker = UltraFastChecker()

@bot.message_handler(commands=['start'])
def start(message):
    welcome = """
⚡ **بوت الفحص فائق السرعة**

🎯 **المميزات:**
• سرعة خيالية: ~20 يوزر/ثانية
• إرسال فوري لكل يوزر متاح
• فحص يوزرات 5-6 أحرف
• بدون Tor (أسرع بأضعاف)

📋 **الأوامر:**
/fast - بدء الفحص فائق السرعة
/stop - إيقاف الفحص  
/stats - إحصائيات فورية
/status - حالة الفحص

🚀 **للبداية:** /fast
"""
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=['fast'])
def start_fast(message):
    """بدء الفحص فائق السرعة"""
    checker.start_ultra_fast_check(message.chat.id)

@bot.message_handler(commands=['stop'])
def stop_fast(message):
    """إيقاف الفحص"""
    checker.stop_check(message.chat.id)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """إحصائيات فورية"""
    if checker.checked_count == 0:
        bot.send_message(message.chat.id, "⚠️ لم يبدأ الفحص بعد")
        return
    
    checker.send_quick_stats()

@bot.message_handler(commands=['status'])
def show_status(message):
    """حالة الفحص"""
    status = checker.get_status()
    bot.send_message(message.chat.id, f"🔍 **الحالة:** {status}")

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    bot.send_message(message.chat.id, "❓ /start للتعليمات")

if __name__ == "__main__":
    print("🚀 تشغيل البوت فائق السرعة...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ خطأ: {e}")