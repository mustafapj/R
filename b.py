import telebot
import time
import threading
import socket
import socks

# إعداد Tor
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
bot = telebot.TeleBot(TOKEN)

class ArayBot:
    def __init__(self):
        self.is_active = False
        self.words = ["مرحبت", "نايمين", "منو يساعدني بشغله", "غ" , "مليت اريد ارتبط😅" , "افتحو الاتصال"]
        self.current_index = 0
        self.group_chat_id = None
        
    def start_sending(self, group_chat_id):
        """بدء إرسال الكلمات في المجموعة"""
        if self.is_active:
            return "⏳ البوت يعمل بالفعل!"
        
        self.is_active = True
        self.group_chat_id = group_chat_id
        self.current_index = 0
        
        # إرسال رسالة البدء في المجموعة
        try:
            bot.send_message(group_chat_id, "🚀 بدأ البوت")
        except Exception as e:
            print(f"خطأ في الإرسال: {e}")
        
        # بدء الإرسال في thread منفصل
        thread = threading.Thread(target=self._sending_loop)
        thread.daemon = True
        thread.start()
        
        return "بدأ البوت العمل 🚀"
    
    def stop_sending(self, group_chat_id):
        """إيقاف إرسال الكلمات"""
        if not self.is_active:
            return "البوت متوقف بالفعل!"
        
        self.is_active = False
        try:
            bot.send_message(group_chat_id, "⏹️ توقف البوت")
        except Exception as e:
            print(f"خطأ في الإرسال: {e}")
        return "تم إيقاف البوت ✅"
    
    def _sending_loop(self):
        """حلقة الإرسال الرئيسية في المجموعة"""
        while self.is_active:
            try:
                # الحصول على الكلمة الحالية
                word = self.words[self.current_index]
                
                # إرسال الكلمة في المجموعة بدون أي إضافات
                bot.send_message(self.group_chat_id, word)
                print(f"✅ تم إرسال في المجموعة: {word}")
                
                # الانتقال للكلمة التالية
                self.current_index = (self.current_index + 1) % len(self.words)
                
                # انتظار 15 ثانية
                for i in range(3):
                    if not self.is_active:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ خطأ في الإرسال: {e}")
                time.sleep(15)

# كائن البوت
aray_bot = ArayBot()

@bot.message_handler(commands=['start'])
def start(message):
    """رسالة الترحيب"""
    welcome = """
🎯 بوت أراي للكلمات

📝 طريقة الاستخدام في المجموعة:
• اراي٢ - بدء إرسال الكلمات
• اراي - إوقف البوت

🔄 الوظيفة:
• يرسل كلمات (كت، نن، ل، غ) في المجموعة
• كل 15 ثانية كلمة جديدة
• بدون أي إضافات أو رموز
"""
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة جميع الرسائل"""
    text = message.text.strip()
    chat_type = message.chat.type
    
    try:
        if text == "اراي٢":
            # بدء البوت في المجموعة
            if chat_type == "group" or chat_type == "supergroup":
                result = aray_bot.start_sending(message.chat.id)
                bot.reply_to(message, result)
            else:
                bot.reply_to(message, "⚠️ هذا الأمر يعمل في المجموعات فقط!")
        
        elif text == "اراي":
            # إيقاف البوت في المجموعة
            if chat_type == "group" or chat_type == "supergroup":
                result = aray_bot.stop_sending(message.chat.id)
                bot.reply_to(message, result)
            else:
                bot.reply_to(message, "⚠️ هذا الأمر يعمل في المجموعات فقط!")
        
        elif chat_type == "private":
            bot.reply_to(message, "❓ أضف البوت للمجموعة ثم اكتب 'اراي٢'")
            
    except Exception as e:
        print(f"❌ خطأ في معالجة الرسالة: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    """ترحيب بالأعضاء الجدد"""
    try:
        for member in message.new_chat_members:
            if member.is_bot and member.username == bot.get_me().username:
                welcome_msg = "🎯 بوت أراي للكلمات\n\nاكتب 'اراي٢' لبدء العمل"
                bot.send_message(message.chat.id, welcome_msg)
                break
    except Exception as e:
        print(f"❌ خطأ في ترحيب الأعضاء: {e}")

if __name__ == "__main__":
    print("🚀 بدء تشغيل بوت أراي عبر Tor...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")