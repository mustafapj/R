import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
DEEPSEEK_API_KEY = "sk-ef7adaec26e9475a847d295ce17ee6f2"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    await update.message.chat.send_action(action="typing")
    
    # المحاولة مع DeepSeek أولاً
    ai_response = await try_deepseek_api(user_message)
    
    # إذا فشل، استخدم ردود بديلة
    if ai_response.startswith("❌") or ai_response.startswith("⚠️"):
        ai_response = get_fallback_response(user_message)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=ai_response
    )

async def try_deepseek_api(message):
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message}],
            "stream": False
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"❌ خطأ API: {response.status_code}"
            
    except Exception as e:
        return f"⚠️ {str(e)}"

def get_fallback_response(message):
    responses = {
        "hello": "👋 أهلاً وسهلاً! للأسف DeepSeek API غير متوفر حالياً.",
        "كيف حالك": "أنا بخير! 😊 البوت يعمل لكن بدون الذكاء الاصطناعي حاليًا.",
        "اسمك": "أنا بوت DeepSeek المساعد 🤖"
    }
    
    msg_lower = message.lower()
    for key, response in responses.items():
        if key in msg_lower:
            return response
    
    return f"🎯 رسالتك: '{message}'\n\n🤖 البوت يعمل! لكن DeepSeek API غير متصل حاليًا."

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
🤖 أهلاً! بوت DeepSeek المساعد

💬 يمكنك:
- سؤال أي استفسار
- المحادثة العادية
- طلب المساعدة

🚦 الحالة: البوت نشط
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Command("start"), start_command))
    
    print("🚀 البوت يعمل...")
    application.run_polling()

if __name__ == "__main__":
    main()