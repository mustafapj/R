import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    
    try:
        # استخدام أحدث نموذج مستقر: gemini-2.0-flash-001
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
        
        response = requests.post(
            url,
            json={
                "contents": [{
                    "parts": [{"text": user_message}]
                }]
            },
            timeout=20
        )
        
        print(f"🔍 API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
        else:
            ai_response = f"❌ خطأ {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        ai_response = f"⚠️ {str(e)}"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 أهلاً بك! بوت الذكاء الاصطناعي

✅ متصل بـ Google Gemini 2.0 Flash
💬 اكتب أي رسالة وسأرد عليك!
"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Command("start"), start_command))
    print("🚀 البوت يعمل مع Gemini 2.0 Flash!")
    application.run_polling()

if __name__ == "__main__":
    main()