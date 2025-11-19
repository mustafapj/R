import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    
    try:
        # الرابط الصحيح لـ Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
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
            ai_response = f"❌ خطأ {response.status_code}: {response.text}"
            
    except Exception as e:
        ai_response = f"⚠️ {str(e)}"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 البوت يعمل مع الرابط المصحح!")
    application.run_polling()

if __name__ == "__main__":
    main()