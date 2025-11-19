import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

# تخزين بيانات المجموعات والوظائف
active_groups = {}
jobs = {}

async def send_group_message(context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة إلى المجموعة كل 5 دقائق"""
    chat_id = context.job.data
    
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
    
    if not update.message or not update.message.text:
        return
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        user_message = update.message.text
        
        await update.message.chat.send_action(action="typing")
        
        try:
            # استخدام Gemini API مع طلب ردود مختصرة
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
            
            prompt = f"أجب على هذا السؤال بإجابة مختصرة ومركزة (بحد أقصى 3 جمل): {user_message}"
            
            response = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
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
    
    # إذا كانت في مجموعة ورداً على البوت
    if update.message.chat.type in ["group", "supergroup"]:
        chat_id = update.message.chat.id
        user_message = update.message.text
        reply_to = update.message.reply_to_message
        
        logger.info(f"🔍 التحقق من الرد في المجموعة {chat_id}")
        logger.info(f"📝 الرسالة: {user_message}")
        logger.info(f"🔄 reply_to: {reply_to}")
        
        # إذا كان رداً على رسالة البوت
        if (reply_to and 
            reply_to.from_user and 
            reply_to.from_user.id == context.bot.id and
            chat_id in active_groups):
            
            logger.info(f"✅ تم التعرف على رد صحيح في المجموعة {chat_id}")
            
            await update.message.chat.send_action(action="typing")
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
                
                # طلب رد مختصر ومركز
                prompt = f"أجب على هذا السؤال بإجابة مختصرة ومركزة (بحد أقصى جملتين): {user_message}"
                
                response = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    full_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # تقصير الرد إذا كان طويلاً
                    if len(full_response) > 200:
                        sentences = full_response.split('.')
                        short_response = '.'.join(sentences[:2]) + '.'
                        ai_response = short_response
                    else:
                        ai_response = full_response
                    
                    response_text = f"👤 {update.message.from_user.first_name}:\n{ai_response}"
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=response_text,
                        reply_to_message_id=update.message.message_id
                    )
                    logger.info(f"✅ تم الرد في المجموعة {chat_id}")
                    
                else:
                    logger.error(f"❌ خطأ API: {response.status_code}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ عذراً، حدث خطأ في الرد",
                        reply_to_message_id=update.message.message_id
                    )
                    
            except Exception as e:
                logger.error(f"⚠️ خطأ في الرد: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ عذراً، حدث خطأ في الرد",
                    reply_to_message_id=update.message.message_id
                )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت في المحادثة الخاصة"""
    await update.message.reply_text(
        "🤖 **أهلاً! أنا البوت المساعد**\n\n"
        "لتفعيل البوت في مجموعة:\n"
        "1. أضفني للمجموعة\n"
        "2. اكتب في المجموعة: /startbot\n\n"
        "سأرسل رسالة كل 5 دقائق وسأرد على الأعضاء! 🚀"
    )

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        # إضافة وظيفة الإرسال التلقائي
        job = context.job_queue.run_repeating(
            send_group_message,
            interval=300,  # كل 5 دقائق
            first=10,      # بعد 10 ثواني
            data=chat_id,
            name=str(chat_id)
        )
        
        jobs[chat_id] = job
        active_groups[chat_id] = None
        
        await update.message.reply_text(
            "✅ **تم تفعيل البوت!**\n\n"
            "سأرسل رسالة كل 5 دقائق وسأرد على أي رد من الأعضاء! 🤖\n"
            "لإيقاف البوت: /stopbot"
        )
        logger.info(f"🚀 تم تفعيل البوت في المجموعة {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تفعيل البوت: {e}")
        await update.message.reply_text("❌ حدث خطأ في تفعيل البوت")

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        # إزالة الوظيفة
        if chat_id in jobs:
            jobs[chat_id].schedule_removal()
            del jobs[chat_id]
        
        if chat_id in active_groups:
            del active_groups[chat_id]
        
        await update.message.reply_text("⏹️ **تم إيقاف البوت!**")
        logger.info(f"⏹️ تم إيقاف البوت في المجموعة {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إيقاف البوت: {e}")
        await update.message.reply_text("❌ حدث خطأ في إيقاف البوت")

def main():
    try:
        # إنشاء التطبيق
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("startbot", start_bot))
        application.add_handler(CommandHandler("stopbot", stop_bot))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
        
        logger.info("🚀 البوت يعمل وجاهز لاستقبال الرسائل...")
        print("🎯 الآن جرب هذه الخطوات في المجموعة:")
        print("1. اكتب: /startbot")
        print("2. انتظر 10 ثواني حتى يرسل البوت رسالة")
        print("3. رد على رسالة البوت")
        print("4. يجب أن يرد عليك البوت بإجابة مختصرة!")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()