import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # القراءة من .env
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# دالة للتحقق من صحة API Key
def check_deepseek_api():
    if not DEEPSEEK_API_KEY:
        return False
        
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Say 'API is working'"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=10)
        return response.status_code == 200
    except:
        return False

# دالة للتواصل مع DeepSeek API
async def get_deepseek_response(user_message):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        elif response.status_code == 401:
            return "❌ API Key غير صالح أو منتهي الصلاحية"
        else:
            return f"⚠️ خطأ في API: {response.status_code}"
            
    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}"

# معالج الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    await update.message.chat.send_action(action="typing")
    
    # الحصول على الرد من DeepSeek
    ai_response = await get_deepseek_response(user_message)
    
    # إرسال الرد
    await update.message.reply_text(ai_response)

# دالة البدء
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التحقق من حالة API
    api_status = "🟢 نشط" if check_deepseek_api() else "🔴 غير نشط"
    
    welcome_text = f"""
🤖 أهلاً بك! بوت DeepSeek الذكي

📊 حالة الخدمات:
✅ Telegram Bot: نشط
{api_status} DeepSeek API: 

اكتب أي سؤال أو رسالة وسأرد عليك!
"""
    await update.message.reply_text(welcome_text)

# الإعدادات الرئيسية
def main():
    # التحقق من التوكن و API قبل البدء
    print("🔍 التحقق من التوكن و API...")
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN غير موجود في .env")
        return
        
    if not DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY غير موجود في .env")
        return
    
    if check_deepseek_api():
        print("✅ DeepSeek API يعمل بشكل صحيح!")
    else:
        print("❌ DeepSeek API غير نشط - تحقق من المفتاح")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Command("start"), start_command))
    
    print("🚀 بدء تشغيل البوت...")
    application.run_polling()

if __name__ == "__main__":
    main()