import telebot
import requests
import random
import string
import time
import logging
from threading import Thread, Lock
import concurrent.futures
import socket
import socks

# إعداد Tor
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket

TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
bot = telebot.TeleBot(TOKEN)

class FastUsernameChecker:
    def __init__(self):
        self.available_users = []
        self.checked_count = 0
        self.is_checking = False
        
    def generate_batch_usernames(self, count):
        """إنشاء مجموعة يوزرات مرة واحدة"""
        characters = string.ascii_lowercase + string.digits + "._"
        return [''.join(random.choice(characters) for _ in range(5)) for _ in range(count)]
    
    def check_username_fast(self, username):
        """فحص سريع لليوزر"""
        url = f"https://t.me/{username}"
        try:
            response = requests.get(url, timeout=5)  # وقت أقل
            return "If you have Telegram" in response.text or "tgme_username_error" in response.text
        except:
            return False
    
    def start_fast_checking(self, chat_id, total_count=100):
        """فحص سريع"""
        if self.is_checking:
            return
            
        self.is_checking = True
        self.available_users = []
        
        def fast_check():
            bot.send_message(chat_id, "⚡ **بدأ الفحص السريع...**")
            
            batch_size = 10  # فحص 10 يوزرات معاً
            checked = 0
            
            while checked < total_count and self.is_checking:
                # إنشاء مجموعة يوزرات
                usernames = self.generate_batch_usernames(batch_size)
                
                # فحص المجموعة
                for username in usernames:
                    if self.check_username_fast(username):
                        self.available_users.append(username)
                        bot.send_message(chat_id, f"🎯 @{username}")
                    
                    checked += 1
                    self.checked_count = checked
                    
                    # تحديث كل 25 يوزر
                    if checked % 25 == 0:
                        bot.send_message(chat_id, f"📊 {checked}/{total_count} - وجد: {len(self.available_users)}")
                
                # تأخير بسيط فقط بين المجموعات
                if checked < total_count:
                    time.sleep(0.1)
            
            # النتائج
            bot.send_message(chat_id, f"✅ **انتهى!**\nفحص: {checked}\nمتاح: {len(self.available_users)}")
            self.is_checking = False
        
        Thread(target=fast_check, daemon=True).start()

checker = FastUsernameChecker()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "⚡ **بوت فحص سريع**\n\n/fast100 - فحص سريع 100 يوزر")

@bot.message_handler(commands=['fast100'])
def fast100(message):
    checker.start_fast_checking(message.chat.id, 100)

@bot.message_handler(commands=['fast200'])
def fast200(message):
    checker.start_fast_checking(message.chat.id, 200)

bot.polling()