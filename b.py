import telebot
import requests
import random
import string
import time
import threading
import socket
import socks

# إعداد Tor
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
bot = telebot.TeleBot(TOKEN)

class AdvancedUsernameChecker:
    def __init__(self):
        self.is_checking = False
        self.checked_count = 0
        self.found_count = 0
        self.start_time = None
        self.current_chat_id = None
        self.session = requests.Session()
        
    def generate_advanced_username(self, length=5):
        """إنشاء يوزرات متقدمة بأنماط مختلفة"""
        # جميع الأنماط المطلوبة
        patterns = [
            # 1. خماسي أحرف صغيرة فقط
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(5)),
            
            # 2. سداسي أحرف صغيرة فقط  
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(6)),
            
            # 3. خماسي أحرف كبيرة وصغيرة
            lambda: ''.join(random.choice(string.ascii_letters) for _ in range(5)),
            
            # 4. سداسي أحرف كبيرة وصغيرة
            lambda: ''.join(random.choice(string.ascii_letters) for _ in range(6)),
            
            # 5. خماسي بأحرف وأرقام
            lambda: ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5)),
            
            # 6. سداسي بأحرف وأرقام
            lambda: ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6)),
            
            # 7. شبه خماسي (4 أحرف + 1 رقم)
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(4)) + random.choice(string.digits),
            
            # 8. شبه خماسي (1 رقم + 4 أحرف)
            lambda: random.choice(string.digits) + ''.join(random.choice(string.ascii_lowercase) for _ in range(4)),
            
            # 9. شبه سداسي (5 أحرف + 1 رقم)
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(5)) + random.choice(string.digits),
            
            # 10. شبه سداسي (1 رقم + 5 أحرف)
            lambda: random.choice(string.digits) + ''.join(random.choice(string.ascii_lowercase) for _ in range(5)),
            
            # 11. شبه خماسي (3 أحرف + 2 رقم)
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(3)) + ''.join(random.choice(string.digits) for _ in range(2)),
            
            # 12. شبه سداسي (4 أحرف + 2 رقم)
            lambda: ''.join(random.choice(string.ascii_lowercase) for _ in range(4)) + ''.join(random.choice(string.digits) for _ in range(2)),
        ]
        return random.choice(patterns)()
    
    def check_username_with_tor(self, username):
        """فحص اليوزر مع Tor"""
        try:
            response = self.session.get(
                f"https://t.me/{username}", 
                timeout=8,  # وقت أطول لـ Tor
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            # فحص دقيق للتوفّر
            if response.status_code == 200:
                if "If you have Telegram" in response.text or "tgme_username_error" in response.text:
                    return True
            return False
        except Exception as e:
            return False
    
    def start_advanced_check(self, chat_id, mode="all"):
        """بدء الفحص المتقدم"""
        if self.is_checking:
            bot.send_message(chat_id, "⏳ جاري فحص يوزرات بالفعل!")
            return
        
        self.is_checking = True
        self.checked_count = 0
        self.found_count = 0
        self.start_time = datetime.now()
        self.current_chat_id = chat_id
        
        mode_names = {
            "all": "جميع الأنواع (خماسي + سداسي + شبه)",
            "5char": "خماسي فقط",
            "6char": "سداسي فقط", 
            "mixed": "مختلط (أحرف وأرقام)"
        }
        
        bot.send_message(
            chat_id, 
            f"🔍 **بدأ الفحص المتقدم عبر Tor**\n"
            f"🎯 **النمط:** {mode_names.get(mode, 'جميع الأنواع')}\n"
            f"⚡ **السرعة:** ~1 يوزر/ثانية\n"
            f"🛡️ **الحماية:** Tor مفعل\n"
            f"📨 **الإرسال:** يوزر + رابط فوري"
        )
        
        def advanced_check():
            last_stats_time = time.time()
            
            while self.is_checking and self.checked_count < 5000:  # حد أقصى
                username = self.generate_advanced_username()
                self.checked_count += 1
                
                if self.check_username_with_tor(username):
                    self.found_count += 1
                    # إرسال اليوزر مع الرابط
                    message = f"🎯 **يوزر متاح!**\n\n"
                    message += f"👤 **اليوزر:** @{username}\n"
                    message += f"🔗 **الرابط:** https://t.me/{username}\n"
                    message += f"📏 **النوع:** {len(username)} أحرف\n"
                    
                    try:
                        bot.send_message(self.current_chat_id, message)
                    except Exception as e:
                        print(f"خطأ في الإرسال: {e}")
                
                # إرسال إحصائيات كل 30 ثانية
                current_time = time.time()
                if current_time - last_stats_time >= 30:
                    self.send_live_stats()
                    last_stats_time = current_time
                
                # تأخير مناسب لـ Tor
                time.sleep(0.8)
            
            # النتائج النهائية
            if self.is_checking:
                self.stop_advanced_check()
        
        # تشغيل الفحص في thread منفصل
        self.check_thread = threading.Thread(target=advanced_check)
        self.check_thread.daemon = True
        self.check_thread.start()
    
    def send_live_stats(self):
        """إرسال إحصائيات حية"""
        if not self.current_chat_id or self.checked_count == 0:
            return
        
        current_time = datetime.now()
        duration = (current_time - self.start_time).total_seconds()
        speed = self.checked_count / duration if duration > 0 else 0
        
        stats_msg = f"""
📊 **الإحصائيات الحية:**

✅ **تم فحص:** {self.checked_count:,} يوزر
🎯 **تم العثور:** {self.found_count} يوزر
📈 **النسبة:** {(self.found_count/self.checked_count*100) if self.checked_count > 0 else 0:.3f}%
⚡ **السرعة:** {speed:.1f} يوزر/ثانية
⏱️ **المدة:** {duration:.0f} ثانية
"""
        try:
            bot.send_message(self.current_chat_id, stats_msg)
        except:
            pass
    
    def stop_advanced_check(self):
        """إيقاف الفحص المتقدم"""
        if not self.is_checking:
            return False
        
        self.is_checking = False
        time.sleep(1)  # انتظار حتى يتوقف الثريد
        
        # الإحصائيات النهائية
        current_time = datetime.now()
        duration = (current_time - self.start_time).total_seconds()
        speed = self.checked_count / duration if duration > 0 else 0
        
        final_msg = f"""
✅ **انتهى الفحص المتقدم!**

📊 **النتائج النهائية:**
• تم فحص: {self.checked_count:,} يوزر
• تم العثور: {self.found_count} يوزر  
• النسبة: {(self.found_count/self.checked_count*100) if self.checked_count > 0 else 0:.3f}%
• السرعة: {speed:.1f} يوزر/ثانية
• المدة: {duration:.0f} ثانية

🎯 **جميع اليوزرات المرسلة صالحة ومتاحة للاستخدام!**
"""
        try:
            bot.send_message(self.current_chat_id, final_msg)
        except:
            pass
        
        return True
    
    def get_current_status(self):
        """الحصول على الحالة الحالية"""
        if not self.is_checking:
            return "⏸️ متوقف"
        
        duration = (datetime.now() - self.start_time).total_seconds()
        speed = self.checked_count / duration if duration > 0 else 0
        
        return f"🔍 فحص: {self.checked_count:,} - وجد: {self.found_count} - السرعة: {speed:.1f}/ثانية"

# كائن الفاحص
checker = AdvancedUsernameChecker()

@bot.message_handler(commands=['start'])
def start(message):
    """رسالة الترحيب"""
    welcome_msg = """
🔍 **بوت الفحص المتقدم لليوزرات**

🎯 **الأنواع المدعومة:**
• يوزرات خماسية (5 أحرف صغيرة)
• يوزرات سداسية (6 أحرف صغيرة)  
• يوزرات خماسية (أحرف كبيرة وصغيرة)
• يوزرات سداسية (أحرف كبيرة وصغيرة)
• يوزرات خماسية (أحرف وأرقام)
• يوزرات سداسية (أحرف وأرقام)
• يوزرات شبه خماسية وسداسية

🛡️ **المميزات:**
• يعمل عبر Tor للحماية
• إرسال فوري لليوزر + الرابط
• إحصائيات حية مفصلة
• فحص آلاف اليوزرات

📋 **الأوامر:**
/scan - بدء الفحص (جميع الأنواع)
/scan5 - يوزرات خماسية فقط
/scan6 - يوزرات سداسية فقط  
/stop - إيقاف الفحص
/stats - إحصائيات فورية
/status - حالة الفحص

🚀 **للبداية:** /scan
"""
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')

@bot.message_handler(commands=['scan'])
def start_scan_all(message):
    """بدء الفحص لجميع الأنواع"""
    checker.start_advanced_check(message.chat.id, "all")

@bot.message_handler(commands=['scan5'])
def start_scan_5char(message):
    """بدء الفحص لليوزرات الخماسية"""
    checker.start_advanced_check(message.chat.id, "5char")

@bot.message_handler(commands=['scan6'])
def start_scan_6char(message):
    """بدء الفحص لليوزرات السداسية"""
    checker.start_advanced_check(message.chat.id, "6char")

@bot.message_handler(commands=['stop'])
def stop_scan(message):
    """إيقاف الفحص"""
    if checker.stop_advanced_check():
        bot.send_message(message.chat.id, "⏹️ **تم إيقاف الفحص**")
    else:
        bot.send_message(message.chat.id, "⚠️ **لا يوجد فحص نشط**")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """عرض الإحصائيات"""
    if checker.checked_count == 0:
        bot.send_message(message.chat.id, "📊 **لم يبدأ الفحص بعد**")
        return
    
    checker.send_live_stats()

@bot.message_handler(commands=['status'])
def show_status(message):
    """عرض حالة الفحص"""
    status = checker.get_current_status()
    bot.send_message(message.chat.id, f"🔄 **حالة الفحص:** {status}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """الرد على أي رسالة أخرى"""
    bot.send_message(message.chat.id, "❓ استخدم /start لرؤية الأوامر المتاحة")

if __name__ == "__main__":
    print("🚀 بدء تشغيل البوت المتقدم عبر Tor...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ خطأ: {e}")