import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# تفعيل التسجيل لرؤية المشاكل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

# تخزين بيانات المجموعات
active_groups = {}

async def send_group_message(context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة إلى المجموعة كل 5 دقائق"""
    chat_id = context.job.chat_id
    
    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="🤖 **البوت المساعد نشط!**\n\nاسألني أي شيء بالرد على هذه الرسالة وسأجيبك فوراً! 💬"
        )
        
        # حفظ آخر رسالة للبوت
        active_groups[chat_id] = message.message_id
        logger.info(f"📤 تم إرسال رسالة إلى المجموعة {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    
    # طباعة معلومات الرسالة للتشخيص
    logger.info(f"📩 رسالة مستلمة: {update.message.text}")
    logger.info(f"👤 من: {update.message.from_user.first_name}")
    logger.info(f"💬 نوع الدردشة: {update.message.chat.type}")
    logger.info(f"🆔 معرف الدردشة: {update.message.chat.id}")
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        user_message = update.message.text
        
        await update.message.chat.send_action(action="typing")
        
        try:
            # استخدام Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
            
            response = requests.post(
                url,
                json={"contents": [{"parts": [{"text": user_message}]}]},
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_response = "❌ حدث خطأ في الخادم"
                
        except Exception as e:
            ai_response = f"⚠️ خطأ: {str(e)}"
        
        await update.message.reply_text(ai_response)
        return
    
    # إذا كانت في مجموعة
    if update.message.chat.type in ["group", "supergroup"]:
        chat_id = update.message.chat.id
        user_message = update.message.text
        reply_to = update.message.reply_to_message
        
        # إذا كان رداً على رسالة البوت
        if (reply_to and 
            reply_to.from_user and 
            reply_to.from_user.id == context.bot.id and
            chat_id in active_groups and
            reply_to.message_id == active_groups[chat_id]):
            
            logger.info(f"🔄 رد من مستخدم في المجموعة: {user_message}")
            
            await update.message.chat.send_action(action="typing")
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
                
                response = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": user_message}]}]},
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    response_text = f"👤 {update.message.from_user.first_name}:\n{ai_response}"
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=response_text,
                        reply_to_message_id=update.message.message_id
                    )
                    logger.info(f"✅ تم الرد في المجموعة {chat_id}")
                    
                else:
                    logger.error(f"❌ خطأ API: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"⚠️ خطأ في الرد: {e}")

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    # إضافة وظيفة الإرسال التلقائي
    context.job_queue.run_repeating(
        send_group_message,
        interval=300,  # كل 5 دقائق
        first=5,       # بعد 5 ثواني
        chat_id=chat_id,
        name=str(chat_id)
    )
    
    active_groups[chat_id] = None
    
    await update.message.reply_text(
        "✅ **تم تفعيل البوت!**\n\n"
        "سأرسل رسالة كل 5 دقائق وسأرد على أي رد من الأعضاء! 🤖"
    )
    logger.info(f"🚀 تم تفعيل البوت في المجموعة {chat_id}")

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    # إزالة الوظيفة
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
    
    if chat_id in active_groups:
        del active_groups[chat_id]
    
    await update.message.reply_text("⏹️ **تم إيقاف البوت!**")
    logger.info(f"⏹️ تم إيقاف البوت في المجموعة {chat_id}")

async def test_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار البوت"""
    await update.message.reply_text("🤖 **البوت يعمل!**\nجرب الرسائل الخاصة أو استخدم /startbot في المجموعة")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة جميع المعالجات
    application.add_handler(CommandHandler("start", test_bot))
    application.add_handler(CommandHandler("startbot", start_bot))
    application.add_handler(CommandHandler("stopbot", stop_bot))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    logger.info("🚀 البوت يعمل وجاهز لاستقبال الرسائل...")
    print("🔍 راقب السجلات لرؤية الرسائل الواردة")
    
    application.run_polling()

if __name__ == "__main__":
    main()