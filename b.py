import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import asyncio

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

# تخزين آخر رسالة للبوت في كل مجموعة
bot_messages = {}

async def send_auto_message(context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة تلقائية كل دقيقة"""
    chat_id = context.job.chat_id
    
    try:
        # إرسال رسالة من البوت
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="🤖 مرحبا بالجميع! أنا البوت المساعد\nاسألني أي شيء بالرد على هذه الرسالة! 💬"
        )
        
        # حفظ معرف الرسالة للبوت
        bot_messages[chat_id] = message.message_id
        print(f"📤 تم إرسال رسالة في المجموعة {chat_id}")
        
    except Exception as e:
        print(f"❌ خطأ في إرسال الرسالة: {e}")

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل في المجموعة"""
    
    # التأكد أن الرسالة في مجموعة وليست محادثة خاصة
    if not update.message or not update.message.chat or update.message.chat.type == "private":
        return
    
    chat_id = update.message.chat.id
    user_message = update.message.text
    reply_to_message = update.message.reply_to_message
    
    # إذا كانت الرسالة رداً على البوت
    if (reply_to_message and 
        reply_to_message.from_user.id == context.bot.id and
        chat_id in bot_messages and
        reply_to_message.message_id == bot_messages[chat_id]):
        
        print(f"🔄 رد من مستخدم في المجموعة {chat_id}: {user_message}")
        
        # إظهار "يكتب..."
        await update.message.chat.send_action(action="typing")
        
        try:
            # استخدام Gemini API للرد
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
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # الرد على المستخدم مع ذكر اسمه
                user_name = update.message.from_user.first_name
                response_text = f"👤 {user_name}:\n{ai_response}"
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=response_text,
                    reply_to_message_id=update.message.message_id
                )
                print(f"✅ تم الرد على المستخدم في المجموعة {chat_id}")
                
            else:
                print(f"❌ خطأ في API: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ خطأ في معالجة الرد: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ عذراً، حدث خطأ في الرد. حاول مرة أخرى!",
                reply_to_message_id=update.message.message_id
            )

async def start_bot_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت في المجموعة (يتم استدعاؤه يدوياً)"""
    chat_id = update.message.chat.id
    
    # إضافة وظيفة إرسال الرسائل التلقائية
    context.job_queue.run_repeating(
        send_auto_message,
        interval=60,  # كل 60 ثانية (دقيقة)
        first=10,     # بعد 10 ثواني من التشغيل
        chat_id=chat_id,
        name=str(chat_id)
    )
    
    await update.message.reply_text(
        "✅ تم تفعيل البوت في هذه المجموعة!\n"
        "سأرسل رسالة كل دقيقة وسترد على أي رد من الأعضاء! 🤖"
    )

async def stop_bot_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    # إيقاف الوظيفة
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    
    # حذف الرسالة المحفوظة
    if chat_id in bot_messages:
        del bot_messages[chat_id]
    
    await update.message.reply_text("⏹️ تم إيقاف البوت في هذه المجموعة!")

def main():
    # إنشاء تطبيق البوت
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS, 
        handle_group_message
    ))
    
    # أوامر التحكم
    application.add_handler(MessageHandler(
        filters.Command("startbot") & filters.ChatType.GROUPS, 
        start_bot_in_group
    ))
    
    application.add_handler(MessageHandler(
        filters.Command("stopbot") & filters.ChatType.GROUPS, 
        stop_bot_in_group
    ))
    
    print("🚀 البوت جاهز للعمل في المجموعات!")
    print("💡 الأوامر المتاحة في المجموعات:")
    print("/startbot - تفعيل البوت")
    print("/stopbot - إيقاف البوت")
    
    application.run_polling()

if __name__ == "__main__":
    main()