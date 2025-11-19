import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# إعدادات Tor Proxy
TOR_PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# دالة للتحقق من عمل Tor
def check_tor_connection():
    try:
        response = requests.get('http://check.torproject.org/', proxies=TOR_PROXIES, timeout=30)
        return "Congratulations" in response.text
    except:
        return False

# دالة للتواصل مع DeepSeek API عبر Tor
async def get_deepseek_response(user_message):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    
    try:
        # التحقق من اتصال Tor أولاً
        if not check_tor_connection():
            return "⚠️ Tor غير نشط. يرجى تشغيل Tor أولاً: `tor &`"
        
        response = requests.post(
            DEEPSEEK_API_URL, 
            headers=headers, 
            json=data, 
            proxies=TOR_PROXIES,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except requests.exceptions.RequestException as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}"
    except Exception as e:
        return f"⚠️ حدث خطأ: {str(e)}"

# معالج الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    # إظهار رسالة "يكتب..."
    await update.message.chat.send_action(action="typing")
    
    # الحصول على الرد من DeepSeek عبر Tor
    ai_response = await get_deepseek_response(user_message)
    
    # إرسال الرد (بتقسيمه إذا كان طويلاً)
    if len(ai_response) > 4096:
        for i in range(0, len(ai_response), 4096):
            await update.message.reply_text(ai_response[i:i+4096])
    else:
        await update.message.reply_text(ai_response)

# دالة البدء
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
    🔒 أهلاً بك! أنا بوت مدعوم بـ DeepSeek
    ⚡ يعمل عبر Tor لحماية الخصوصية
    
    فقط اكتب رسالتك وسأرد عليك فوراً!
    """
    await update.message.reply_text(welcome_text)

# دالة حالة Tor
async def tor_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "🟢 Tor نشط" if check_tor_connection() else "🔴 Tor غير نشط"
    await update.message.reply_text(f"حالة Tor: {status}")

# الإعدادات الرئيسية
def main():
    # التحقق من تشغيل Tor
    if not check_tor_connection():
        print("⚠️ تحذير: Tor غير نشط. تشغيل البوت بدون حماية...")
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # الأوامر
    application.add_handler(MessageHandler(filters.Command("start"), start_command))
    application.add_handler(MessageHandler(filters.Command("tor"), tor_status))
    
    # بدء البوت
    print("🤖 البوت يعمل الآن مع Tor...")
    application.run_polling()

if __name__ == "__main__":
    main()