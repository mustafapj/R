import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# التوكن والمفاتيح مباشرة في الكود
TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
DEEPSEEK_API_KEY = "sk-9c52f37206c24fd39502d5a6d71fb406"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

print("=" * 50)
print("🔍 التحقق من الإعدادات...")
print(f"✅ Token: {TELEGRAM_TOKEN[:10]}...")
print(f"✅ API Key: {DEEPSEEK_API_KEY[:10]}...")
print("=" * 50)

# دالة للتحقق من صحة API Key
def check_deepseek_api():
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
    
    # إظهار "يكتب..."
    await update.message.chat.send_action(action="typing")
    
    # الحصول على الرد من DeepSeek
    ai_response = await get_deepseek_response(user_message)
    
    # إرسال الرد (بتقسيمه إذا كان طويلاً)
    if len(ai_response) > 4096:
        for i in range(0, len(ai_response), 4096):
            await update.message.reply_text(ai_response[i:i+4096])
    else:
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

اكتب أي سؤال أو رسالة وسأرد عليك فوراً! 🚀
"""
    await update.message.reply_text(welcome_text)

# أمر المساعدة
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📝 **الأوامر المتاحة:**
/start - بدء البوت ورؤية الحالة
/help - عرض هذه المساعدة

💬 **يمكنك أيضاً:**
- سؤال أي استفسار
- طلب المساعدة في البرمجة
- الترجمة بين اللغات
- كتابة النصوص
- حل المسائل الرياضية
"""
    await update.message.reply_text(help_text)

# الإعدادات الرئيسية
def main():
    # التحقق من API قبل البدء
    print("🔍 التحقق من DeepSeek API...")
    if check_deepseek_api():
        print("✅ DeepSeek API يعمل بشكل صحيح!")
    else:
        print("❌ DeepSeek API غير نشط - تحقق من المفتاح")
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Command("start"), start_command))
    application.add_handler(MessageHandler(filters.Command("help"), help_command))
    
    # بدء البوت
    print("🚀 البوت يعمل الآن...")
    print("💬 اذهب إلى تليجرام وجرب البوت!")
    application.run_polling()

if __name__ == "__main__":
    main()