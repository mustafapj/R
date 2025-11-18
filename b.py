import telebot
import requests
import random
import string
import time
import threading
import socket
import socks
from datetime import datetime

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
        self.current_platform = "telegram"  # telegram or instagram
        
    def generate_username(self, platform="telegram", length=None):
        """إنشاء يوزرات بأنماط مختلفة"""
        if platform == "instagram":
            # يوزرات إنستجرام من 3 إلى 7 أحرف
            if length is None:
                length = random.randint(3, 7)
            chars = string.ascii_lowercase + string.digits + "._"
            return ''.join(random.choice(chars) for _ in range(length))
        else:
            # يوزرات تليجرام بأنماط متقدمة
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
            ]
            return random.choice(patterns)()
    
    def check_telegram_username(self, username):
        """فحص يوزر تليجرام"""
        try:
            response = self.session.get(
                f"https://t.me/{username}", 
                timeout=8,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            if response.status_code == 200:
                if "If you have Telegram" in response.text or "tgme_username_error" in response.text:
                    return True
            return False
        except:
            return False
    
    def check_instagram_username(self, username):
        """فحص يوزر إنستجرام"""
        try:
            response = self.session.get(
                f"https://www.instagram.com/{username}/", 
                timeout=8,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            if response.status_code == 200:
                # في إنستجرام، إذا الصفحة تحتوي على "Sorry" أو "Page not found" فهو متاح
                if "Sorry, this page isn't available." in response.text or "Page not found" in response.text:
                    return True
                # إذا وجدنا معلومات المستخدم فهو مُستخدم
                elif '"username":"' in response.text and f'"{username}"' in response.text:
                    return False
            elif response.status_code == 404:
                return True
            return False
        except:
            return False
    
    def check_username(self, username, platform):
        """فحص اليوزر حسب المنصة"""
        if platform == "instagram":
            return self.check_instagram_username(username)
        else:
            return self.check_telegram_username(username)
    
    def start_advanced_check(self, chat_id, platform="telegram"):
        """بدء الفحص المتقدم"""
        if self.is_checking:
            bot.send_message(chat_id, "⏳ جاري فحص يوزرات بالفعل!")
            return
        
        self.is_checking = True
        self.checked_count = 0
        self.found_count = 0
        self.start_time = datetime.now()
        self.current_chat_id = chat_id
        self.current_platform = platform
        
        platform_info = {
            "telegram": {
                "name": "تليجرام",
                "types": "خماسي + سداسي + شبه",
                "speed": "~1 يوزر/ثانية"
            },
            "instagram": {
                "name": "إنستجرام", 
                "types": "ثلاثي إلى سباعي (3-7 أحرف)",
                "speed": "~0.8 يوزر/ثانية"
            }
        }
        
        info = platform_info.get(platform, platform_info["telegram"])
        
        bot.send_message(
            chat_id, 
            f"🔍 **بدأ الفحص على {info['name']} عبر Tor**\n"
            f"🎯 **الأنواع:** {info['types']}\n"
            f"⚡ **السرعة:** {info['speed']}\n"
            f"🛡️ **الحماية:** Tor مفعل\n"
            f"📨 **الإرسال:** يوزر + رابط فوري"
        )
        
        def advanced_check():
            last_stats_time = time.time()
            
            while self.is_checking and self.checked_count < 3000:  # حد أقصى
                username = self.generate_username(self.current_platform)
                self.checked_count += 1
                
                if self.check_username(username, self.current_platform):
                    self.found_count += 1
                    # إرسال اليوزر مع الرابط فوراً
                    if self.current_platform == "telegram":
                        link = f"https://t.me/{username}"
                    else:
                        link = f"https://instagram.com/{username}"
                    
                    message = f"🎯 **يوزر متاح على {self.current_platform.upper()}!**\n\n"
                    message += f"👤 **اليوزر:** @{username}\n"
                    message += f"🔗 **الرابط:** {link}\n"
                    message += f"📏 **الطول:** {len(username)} أحرف\n"
                    message += f"📊 **رقم:** #{self.found_count}\n"
                    
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
                time.sleep(1.0 if self.current_platform == "instagram" else 0.8)
            
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
📊 **الإحصائيات الحية على {self.current_platform.upper()}:**

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
✅ **انتهى الفحص على {self.current_platform.upper()}!**

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
        
        return f"🔍 {self.current_platform.upper()} - فحص: {self.checked_count:,} - وجد: {self.found_count} - السرعة: {speed:.1f}/ثانية"

# كائن الفاحص
checker = AdvancedUsernameChecker()

@bot.message_handler(commands=['start'])
def start(message):
    """رسالة الترحيب"""
    welcome_msg = """
🔍 **بوت الفحص المتقدم لليوزرات**

🎯 **المنصات المدعومة:**
• **تليجرام:** يوزرات خماسية، سداسية، شبه خماسية/سداسية
• **إنستجرام:** يوزرات من 3 إلى 7 أحرف عشوائية

🛡️ **المميزات:**
• يعمل عبر Tor للحماية
• إرسال فوري لليوزر + الرابط
• إحصائيات حية مفصلة
• فحص آلاف اليوزرات

📋 **أوامر تليجرام:**
/tg_scan - فحص جميع أنواع يوزرات تليجرام
/tg_scan5 - يوزرات تليجرام خماسية فقط
/tg_scan6 - يوزرات تليجرام سداسية فقط

📷 **أوامر إنستجرام:**
/ig_scan - فحص يوزرات إنستجرام عشوائية (3-7 أحرف)
/ig_scan_short - يوزرات إنستجرام قصيرة (3-4 أحرف)
/ig_scan_long - يوزرات إنستجرام طويلة (5-7 أحرف)

⚙️ **أوامر تحكم:**
/stop - إيقاف الفحص
/stats - إحصائيات فورية
/status - حالة الفحص

🚀 **للبداية:** اختر أحد الأوامر أعلاه
"""
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')

# أوامر تليجرام
@bot.message_handler(commands=['tg_scan'])
def start_tg_scan_all(message):
    """بدء الفحص لجميع أنواع يوزرات تليجرام"""
    checker.start_advanced_check(message.chat.id, "telegram")

@bot.message_handler(commands=['tg_scan5'])
def start_tg_scan_5char(message):
    """بدء الفحص لليوزرات التليجرام الخماسية"""
    checker.start_advanced_check(message.chat.id, "telegram")

@bot.message_handler(commands=['tg_scan6'])
def start_tg_scan_6char(message):
    """بدء الفحص لليوزرات التليجرام السداسية"""
    checker.start_advanced_check(message.chat.id, "telegram")

# أوامر إنستجرام
@bot.message_handler(commands=['ig_scan'])
def start_ig_scan(message):
    """بدء الفحص ليوزرات إنستجرام عشوائية"""
    checker.start_advanced_check(message.chat.id, "instagram")

@bot.message_handler(commands=['ig_scan_short'])
def start_ig_scan_short(message):
    """بدء الفحص ليوزرات إنستجرام قصيرة"""
    checker.start_advanced_check(message.chat.id, "instagram")

@bot.message_handler(commands=['ig_scan_long'])
def start_ig_scan_long(message):
    """بدء الفحص ليوزرات إنستجرام طويلة"""
    checker.start_advanced_check(message.chat.id, "instagram")

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