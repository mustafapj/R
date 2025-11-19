import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"  # ضعه هنا

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action="typing")
    
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            json={
                "contents": [{
                    "parts": [{"text": user_message}]
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['candidates'][0]['content']['parts'][0]['text']
        else:
            ai_response = "❌ حدث خطأ في الاتصال"
            
    except Exception as e:
        ai_response = f"⚠️ خطأ: {str(e)}"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=ai_response)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 البوت يعمل مع Gemini API!")
    application.run_polling()

if __name__ == "__main__":
    main()