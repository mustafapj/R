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
bot_messages = {}

async def send_group_message(chat_id, context):
    """إرسال رسالة إلى المجموعة كل 2-3 دقائق"""
    try:
        while chat_id in active_groups:
            # استخدام العبارات من الملف المستقل
            phrase = random.choice(IRAQI_PHRASES)
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=phrase
            )
            
            # حفظ الرسالة في قائمة آخر رسائل البوت
            if chat_id not in bot_messages:
                bot_messages[chat_id] = []
            
            bot_messages[chat_id].append(message.message_id)
            
            # الاحتفاظ بآخر 10 رسائل فقط
            if len(bot_messages[chat_id]) > 10:
                bot_messages[chat_id] = bot_messages[chat_id][-10:]
            
            logger.info(f"📤 تم إرسال رسالة إلى المجموعة {chat_id}: {phrase}")
            
            # انتظر 2-3 دقائق عشوائياً
            await asyncio.sleep(random.randint(120, 180))
            
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")

async def handle_ai_response(user_message, reply_to_message_id, chat_id, context):
    """معالجة الرد من الذكاء الاصطناعي"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"أجب بإجابة مختصرة جداً (جملة واحدة) باللهجة العراقية: {user_message}"
        
        logger.info(f"🔄 جاري إرسال طلب إلى API: {user_message}")
        
        response = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15
        )
        
        logger.info(f"📡 استجابة API: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            full_response = result['candidates'][0]['content']['parts'][0]['text']
            
            # تقصير الرد
            if len(full_response) > 100:
                sentences = full_response.split('.')
                ai_response = '.'.join(sentences[:1]) + '.'
            else:
                ai_response = full_response
            
            logger.info(f"✅ الرد النهائي: {ai_response}")
            
            # إرسال الرد
            await context.bot.send_message(
                chat_id=chat_id,
                text=ai_response,
                reply_to_message_id=reply_to_message_id
            )
            logger.info(f"✅ تم الرد في المجموعة {chat_id}")
            
        else:
            logger.error(f"❌ خطأ API: {response.status_code} - {response.text}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="😊 آسف، حاول مرة ثانية",
                reply_to_message_id=reply_to_message_id
            )
            
    except Exception as e:
        logger.error(f"❌ خطأ في الرد: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="😊 آسف، حاول مرة ثانية",
            reply_to_message_id=reply_to_message_id
        )

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    
    if not update.message or not update.message.text:
        return
    
    user_message = update.message.text
    chat_id = update.message.chat.id
    
    logger.info(f"📩 رسالة مستلمة في {chat_id}: {user_message}")
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        await update.message.chat.send_action(action=ChatAction.TYPING)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
            
            prompt = f"أجب بإجابة مختصرة باللهجة العراقية: {user_message}"
            
            response = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
            else:
                ai_response = "❌ حدث خطأ"
                
        except Exception as e:
            ai_response = "⚠️ معليش، ما قدرت أرد هسه"
        
        await update.message.reply_text(ai_response)
        return
    
    # إذا كانت في مجموعة
    if update.message.chat.type in ["group", "supergroup"]:
        reply_to = update.message.reply_to_message
        
        logger.info(f"🔍 التحقق من الرسالة في المجموعة {chat_id}")
        logger.info(f"📝 الرسالة: {user_message}")
        logger.info(f"🔄 reply_to: {reply_to}")
        logger.info(f"📋 bot_messages: {bot_messages.get(chat_id, [])}")
        
        # التحقق إذا كان رداً على أي رسالة للبوت
        is_reply_to_bot = False
        if reply_to and reply_to.from_user:
            logger.info(f"👤 مرسل الرسالة الأصلية: {reply_to.from_user.id}")
            logger.info(f"🤖 البوت: {context.bot.id}")
            
            if reply_to.from_user.id == context.bot.id:
                logger.info("✅ الرسالة موجهة للبوت!")
                if chat_id in bot_messages:
                    if reply_to.message_id in bot_messages[chat_id]:
                        is_reply_to_bot = True
                        logger.info("✅ الرسالة معروفة للبوت!")
                    else:
                        logger.info("❌ الرسالة غير معروفة للبوت")
                else:
                    logger.info("❌ لا توجد رسائل محفوظة للبوت في هذه المجموعة")
        
        # التحقق إذا كان مناداة مباشرة
        is_mention = False
        mention_keywords = ["قمر", "@userhak_bot"]
        if any(keyword in user_message.lower() for keyword in mention_keywords):
            is_mention = True
            logger.info("✅ تم التعرف على مناداة مباشرة!")
        
        # إذا كان رداً على البوت أو مناداة مباشرة
        if is_reply_to_bot or is_mention:
            logger.info(f"🎯 تفاعل صحيح في المجموعة {chat_id}")
            
            # إظهار "يكتب..." فوراً
            await update.message.chat.send_action(action=ChatAction.TYPING)
            
            # معالجة الرد في مهمة منفصلة
            asyncio.create_task(
                handle_ai_response(
                    user_message, 
                    update.message.message_id, 
                    chat_id, 
                    context
                )
            )
        else:
            logger.info("❌ لا يوجد تفاعل مع البوت")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت في المحادثة الخاصة"""
    await update.message.reply_text(
        "🤖 **أهلاً! أنا البوت قمر**\n\n"
        "لتفعيل البوت في مجموعة:\n"
        "1. أضفني للمجموعة\n"
        "2. اكتب في المجموعة: /startbot\n\n"
        "سأرسل رسالة كل 2-3 دقائق وسأرد على الأعضاء! 🚀"
    )

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        # إيقاف أي مهمة سابقة
        if chat_id in group_tasks:
            group_tasks[chat_id].cancel()
        
        # تفعيل المجموعة
        active_groups[chat_id] = True
        bot_messages[chat_id] = []
        
        # إرسال أول رسالة فوراً
        phrase = random.choice(IRAQI_PHRASES)
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=phrase
        )
        bot_messages[chat_id].append(message.message_id)
        
        # بدء المهمة التلقائية
        task = asyncio.create_task(send_group_message(chat_id, context))
        group_tasks[chat_id] = task
        
        await update.message.reply_text(
            "✅ **تم تفعيل البوت قمر!**\n\n"
            "سأرسل رسالة كل 2-3 دقائق وسأرد على أي رد أو مناداة! 🤖\n"
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
        
        if chat_id in bot_messages:
            del bot_messages[chat_id]
        
        await update.message.reply_text("⏹️ **تم إيقاف البوت قمر!**")
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
        
        logger.info("🚀 البوت قمر يعمل...")
        print("✅ البوت قمر جاهز! الميزات:")
        print(f"🎯 {len(IRAQI_PHRASES)} عبارة عراقية")
        print("⏰ يرسل كل 2-3 دقائق")
        print("💬 يرد على الردود والمناداة (قمر، @userhak_bot)")
        print("🔍 تسجيل مفصل للأخطاء")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ في التشغيل: {e}")

if __name__ == "__main__":
    main()