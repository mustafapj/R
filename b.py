import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # التصحيح هنا

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

# تخزين بيانات المجموعات
active_groups = {}
group_tasks = {}

async def send_group_message(chat_id, context):
    """إرسال رسالة إلى المجموعة كل 5 دقائق"""
    try:
        while chat_id in active_groups:
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="🤖 **البوت المساعد نشط!**\n\nاسألني أي شيء بالرد على هذه الرسالة وسأجيبك فوراً! 💬"
            )
            
            # حفظ آخر رسالة للبوت
            active_groups[chat_id] = message.message_id
            logger.info(f"📤 تم إرسال رسالة إلى المجموعة {chat_id}")
            
            # انتظر 5 دقائق
            await asyncio.sleep(300)
            
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    
    if not update.message or not update.message.text:
        return
    
    logger.info(f"📩 رسالة: {update.message.text}")
    logger.info(f"💬 نوع: {update.message.chat.type}")
    logger.info(f"🆔 معرف: {update.message.chat.id}")
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        user_message = update.message.text
        
        await update.message.chat.send_action(action="typing")
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
            
            prompt = f"أجب بإجابة مختصرة (جملة أو اثنتين): {user_message}"
            
            response = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_response = "❌ حدث خطأ"
                
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
            
            logger.info(f"✅ تم التعرف على رد صحيح في المجموعة")
            
            await update.message.chat.send_action(action="typing")
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
                
                prompt = f"أجب بإجابة مختصرة جداً (جملة واحدة): {user_message}"
                
                response = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    full_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # تقصير الرد
                    if len(full_response) > 100:
                        sentences = full_response.split('.')
                        ai_response = '.'.join(sentences[:1]) + '.'
                    else:
                        ai_response = full_response
                    
                    response_text = f"👤 {update.message.from_user.first_name}:\n{ai_response}"
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=response_text,
                        reply_to_message_id=update.message.message_id
                    )
                    logger.info(f"✅ تم الرد في المجموعة")
                    
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ عذراً، حدث خطأ",
                        reply_to_message_id=update.message.message_id
                    )
                    
            except Exception as e:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ عذراً، حدث خطأ",
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
        # إيقاف أي مهمة سابقة
        if chat_id in group_tasks:
            group_tasks[chat_id].cancel()
        
        # تفعيل المجموعة
        active_groups[chat_id] = None
        
        # إرسال أول رسالة فوراً
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="🤖 **البوت المساعد نشط!**\n\nاسألني أي شيء بالرد على هذه الرسالة وسأجيبك فوراً! 💬"
        )
        active_groups[chat_id] = message.message_id
        
        # بدء المهمة التلقائية
        task = asyncio.create_task(send_group_message(chat_id, context))
        group_tasks[chat_id] = task
        
        await update.message.reply_text(
            "✅ **تم تفعيل البوت!**\n\n"
            "سأرسل رسالة كل 5 دقائق وسأرد على أي رد من الأعضاء! 🤖\n"
            "لإيقاف البوت: /stopbot"
        )
        logger.info(f"🚀 تم تفعيل البوت في المجموعة {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تفعيل البوت: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        # إيقاف المهمة
        if chat_id in group_tasks:
            group_tasks[chat_id].cancel()
            del group_tasks[chat_id]
        
        if chat_id in active_groups:
            del active_groups[chat_id]
        
        await update.message.reply_text("⏹️ **تم إيقاف البوت!**")
        logger.info(f"⏹️ تم إيقاف البوت في المجموعة {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إيقاف البوت: {e}")
        await update.message.reply_text("❌ حدث خطأ في إيقاف البوت")

def main():
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("startbot", start_bot))
        application.add_handler(CommandHandler("stopbot", stop_bot))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
        
        logger.info("🚀 البوت يعمل...")
        print("✅ جرب في المجموعة:")
        print("1. /startbot - سيرسل رسالة فوراً")
        print("2. رد على رسالة البوت")
        print("3. /stopbot - لإيقاف البوت")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()