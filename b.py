import telebot
import time
import threading
from datetime import datetime

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
bot = telebot.TeleBot(TOKEN)

class ArayBot:
    def __init__(self):
        self.is_active = False
        self.words = ["كت", "نن", "ل", "غ"]
        self.current_index = 0
        self.group_chat_id = None
        self.user_chat_id = None
        
    def start_sending(self, group_chat_id, user_chat_id):
        """بدء إرسال الكلمات"""
        if self.is_active:
            return "البوت يعمل بالفعل!"
        
        self.is_active = True
        self.group_chat_id = group_chat_id
        self.user_chat_id = user_chat_id
        
        # إرسال رسالة البدء
        bot.send_message(user_chat_id, "🎯 بدأ البوت في إرسال الكلمات كل 15 ثانية")
        
        # بدء الإرسال في thread منفصل
        thread = threading.Thread(target=self._sending_loop)
        thread.daemon = True
        thread.start()
        
        return "بدأ البوت العمل 🚀"
    
    def stop_sending(self, user_chat_id):
        """إيقاف إرسال الكلمات"""
        if not self.is_active:
            return "البوت متوقف بالفعل!"
        
        self.is_active = False
        bot.send_message(user_chat_id, "⏹️ توقف البوت عن الإرسال")
        return "تم إيقاف البوت ✅"
    
    def _sending_loop(self):
        """حلقة الإرسال الرئيسية"""
        while self.is_active:
            try:
                # الحصول على الكلمة الحالية
                word = self.words[self.current_index]
                
                # إرسال الكلمة على انفراد للمستخدم
                bot.send_message(self.user_chat_id, f"📨 {word}")
                
                # الانتقال للكلمة التالية
                self.current_index = (self.current_index + 1) % len(self.words)
                
                # انتظار 15 ثانية
                for i in range(15):
                    if not self.is_active:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"خطأ في الإرسال: {e}")
                time.sleep(15)

# كائن البوت
aray_bot = ArayBot()

@bot.message_handler(commands=['start'])
def start(message):
    """رسالة الترحيب"""
    welcome = """
🎯 **بوت أراي للكلمات**

📝 **طريقة الاستخدام:**
1. أضف البوت لمجموعتك
2. في المجموعة، اكتب:
   - `اراي` ⏹️ لإيقاف البوت
   - `اراي٢` 🚀 لبدء البوت

🔄 **وظيفة البوت:**
• يرسل كلمات (كت، نن، ل، غ) كل 15 ثانية
• الإرسال على انفراد لك
• يمكن التحكم به من المجموعة

🚀 **للبداية:** اكتب في المجموعة `اراي٢`
"""
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة جميع الرسائل"""
    text = message.text.strip().lower()
    chat_type = message.chat.type
    
    try:
        if text == "اراي٢":
            # بدء البوت
            if chat_type == "group" or chat_type == "supergroup":
                result = aray_bot.start_sending(message.chat.id, message.from_user.id)
                bot.reply_to(message, result)
            else:
                bot.reply_to(message, "⚠️ هذا الأمر يعمل في المجموعات فقط!")
        
        elif text == "اراي":
            # إيقاف البوت
            if chat_type == "group" or chat_type == "supergroup":
                result = aray_bot.stop_sending(message.from_user.id)
                bot.reply_to(message, result)
            else:
                bot.reply_to(message, "⚠️ هذا الأمر يعمل في المجموعات فقط!")
        
        elif chat_type == "private":
            bot.reply_to(message, "❓ اكتب /start للمساعدة")
            
    except Exception as e:
        print(f"خطأ: {e}")
        bot.reply_to(message, "❌ حدث خطأ، حاول مرة أخرى")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_members(message):
    """ترحيب بالأعضاء الجدد"""
    for member in message.new_chat_members:
        if member.is_bot and member.username == bot.get_me().username:
            welcome_msg = """
🎯 **بوت أراي للكلمات انضم للمجموعة**

📝 **الأوامر المتاحة:**
• `اراي٢` - بدء إرسال الكلمات
• `اراي` - إيقاف الإرسال

🔄 **الوظيفة:** يرسل كلمات كل 15 ثانية على انفراد
"""
            bot.send_message(message.chat.id, welcome_msg)
            break

if __name__ == "__main__":
    print("🚀 بدء تشغيل بوت أراي...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ خطأ: {e}")