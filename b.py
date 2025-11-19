import requests
import random
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# استيراد العبارات من ملف منفصل
from phrases import IRAQI_PHRASES

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

# تخزين البيانات
active_groups = {}
group_tasks = {}
current_phrases = {}

async def send_group_message(chat_id, context):
    """إرسال رسالة إلى المجموعة كل 3 دقائق"""
    try:
        while chat_id in active_groups:
            # استخدام العبارات من الملف المستقل
            current_phrases[chat_id] = random.choice(IRAQI_PHRASES)
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=current_phrases[chat_id]
            )
            
            active_groups[chat_id] = message.message_id
            logger.info(f"📤 تم إرسال رسالة إلى المجموعة {chat_id}")
            
            # انتظر 3 دقائق
            await asyncio.sleep(180)
            
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    
    if not update.message or not update.message.text:
        return
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        user_message = update.message.text
        
        await update.message.chat.send_action(action=ChatAction.TYPING)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
            
            prompt = f"أجب بإجابة مختصرة جداً (جملة واحدة أو اثنتين كحد أقصى) باللهجة العراقية: {user_message}"
            
            response = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                full_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # تقصير الرد
                if len(full_response) > 100:
                    sentences = full_response.split('.')
                    ai_response = '.'.join(sentences[:2]) + '.'
                else:
                    ai_response = full_response
            else:
                ai_response = "❌ حدث خطأ"
                
        except Exception as e:
            ai_response = "⚠️ معليش، ما قدرت أرد هسه"
        
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
            
            logger.info(f"✅ تم التعرف على رد صحيح في المجموعة: {user_message}")
            
            await update.message.chat.send_action(action=ChatAction.TYPING)
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
                
                prompt = f"أجب بإجابة مختصرة جداً (جملة واحدة) باللهجة العراقية: {user_message}"
                
                response = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=15
                )
                
                logger.info(f"🔍 حالة الرد من API: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    full_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # تقصير الرد
                    if len(full_response) > 80:
                        sentences = full_response.split('.')
                        ai_response = '.'.join(sentences[:1]) + '.'
                    else:
                        ai_response = full_response
                    
                    logger.info(f"📝 الرد النهائي: {ai_response}")
                    
                    # إرسال الرد بدون ذكر الاسم
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=ai_response,
                        reply_to_message_id=update.message.message_id
                    )
                    logger.info(f"✅ تم الرد في المجموعة")
                    
                else:
                    error_msg = f"❌ خطأ API: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="😊 آسف، حاول مرة ثانية",
                        reply_to_message_id=update.message.message_id
                    )
                    
            except Exception as e:
                error_msg = f"❌ خطأ في الاتصال: {e}"
                logger.error(error_msg)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="😊 آسف، حاول مرة ثانية",
                    reply_to_message_id=update.message.message_id
                )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت في المحادثة الخاصة"""
    await update.message.reply_text(
        "🤖 **أهلاً! أنا البوت المساعد**\n\n"
        "لتفعيل البوت في مجموعة:\n"
        "1. أضفني للمجموعة\n"
        "2. اكتب في المجموعة: /startbot\n\n"
        "سأرسل رسالة كل 3 دقائق وسأرد على الأعضاء! 🚀"
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
        current_phrases[chat_id] = random.choice(IRAQI_PHRASES)
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=current_phrases[chat_id]
        )
        active_groups[chat_id] = message.message_id
        
        # بدء المهمة التلقائية
        task = asyncio.create_task(send_group_message(chat_id, context))
        group_tasks[chat_id] = task
        
        await update.message.reply_text(
            "✅ **تم تفعيل البوت!**\n\n"
            "سأرسل رسالة كل 3 دقائق وسأرد على أي رد من الأعضاء! 🤖\n"
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
        
        if chat_id in current_phrases:
            del current_phrases[chat_id]
        
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
        print("✅ البوت جاهز! الميزات:")
        print(f"🎯 {len(IRAQI_PHRASES)} عبارة عراقية - تتغير كل 3 دقائق")
        print("⚡ ردود سريعة بدون أسماء")
        print("💬 يدعم المحادثات الخاصة والمجموعات")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()