import requests
import random
import asyncio
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# استيراد الملفات
from phrases import IRAQI_PHRASES
from simple_qa import SIMPLE_QA, GENERAL_QUESTIONS  # الملف الجديد

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"

# تخزين البيانات
active_groups = {}
group_tasks = {}
bot_messages = {}
user_last_message = {}  # تخزين آخر رسالة لكل مستخدم

async def set_bot_commands(application):
    """تعيين أوامر البوت في القائمة"""
    commands = [
        BotCommand("start", "بدء البوت"),
        BotCommand("help", "المساعدة"),
        BotCommand("startbot", "تشغيل البوت في المجموعة"),
        BotCommand("stopbot", "إيقاف البوت في المجموعة"),
        BotCommand("status", "حالة البوت")
    ]
    await application.bot.set_my_commands(commands)

def get_local_answer(user_message, user_id):
    """البحث في الإجابات المحلية أولاً"""
    user_message = user_message.strip().lower()
    
    # البحث المباشر في الأسئلة
    if user_message in SIMPLE_QA:
        user_last_message[user_id] = user_message
        return SIMPLE_QA[user_message]
    
    # إذا كان رد على الإجابة السابقة
    if user_id in user_last_message:
        last_msg = user_last_message[user_id]
        if last_msg in SIMPLE_QA:
            previous_answer = SIMPLE_QA[last_msg]
            if user_message == previous_answer.lower():
                user_last_message[user_id] = user_message
                # إرجاع إجابة إضافية إذا موجودة
                if previous_answer in SIMPLE_QA:
                    return SIMPLE_QA[previous_answer]
    
    # التحقق إذا كان سؤال عام يحتاج AI
    for word in GENERAL_QUESTIONS:
        if word in user_message:
            return None
    
    return "اسأل 'ش تدرس' أو 'شكد عمرج' علشان افهم سؤالك"

async def handle_ai_response(user_message, reply_to_message_id, chat_id, context):
    """معالجة الرد من الذكاء الاصطناعي"""
    try:
        user_id = f"{chat_id}_{reply_to_message_id}"
        
        # البحث في الإجابات المحلية أولاً
        local_answer = get_local_answer(user_message, user_id)
        
        if local_answer and local_answer != "اسأل 'ش تدرس' أو 'شكد عمرج' علشان افهم سؤالك":
            ai_response = local_answer
            logger.info(f"✅ استخدام الإجابة المحلية: {ai_response}")
        elif local_answer and "اسأل" in local_answer:
            ai_response = local_answer
            logger.info(f"✅ توجيه لسؤال أفضل: {ai_response}")
        else:
            # استخدام Gemini AI فقط إذا لم توجد إجابة محلية
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
            
            prompt = f"أجب بإجابة مختصرة جداً (جملة واحدة) باللهجة العراقية: {user_message}"
            
            response = requests.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=15
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
                
                logger.info(f"✅ استخدام Gemini AI: {ai_response}")
            else:
                ai_response = "😊 آسف، حاول مرة ثانية"
        
        # حفظ رسالة الرد في القائمة
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=ai_response,
            reply_to_message_id=reply_to_message_id
        )
        
        # حفظ رسالة الرد في القائمة
        if chat_id not in bot_messages:
            bot_messages[chat_id] = []
        bot_messages[chat_id].append(message.message_id)
        
        # الاحتفاظ بآخر 15 رسائل فقط
        if len(bot_messages[chat_id]) > 15:
            bot_messages[chat_id] = bot_messages[chat_id][-15:]
        
        logger.info(f"✅ تم الرد وحفظ الرسالة {message.message_id}")
        
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text="😊 آسف، حاول مرة ثانية",
            reply_to_message_id=reply_to_message_id
        )

async def send_group_message(chat_id, context):
    """إرسال رسالة إلى المجموعة كل 2-3 دقائق"""
    try:
        while chat_id in active_groups and active_groups[chat_id]:
            phrase = random.choice(IRAQI_PHRASES)
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=phrase
            )
            
            # حفظ الرسالة
            if chat_id not in bot_messages:
                bot_messages[chat_id] = []
            bot_messages[chat_id].append(message.message_id)
            
            # الاحتفاظ بآخر 15 رسائل
            if len(bot_messages[chat_id]) > 15:
                bot_messages[chat_id] = bot_messages[chat_id][-15:]
            
            logger.info(f"📤 أرسل: {message.message_id}")
            await asyncio.sleep(random.randint(120, 180))
            
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    
    if not update.message or not update.message.text:
        return
    
    user_message = update.message.text
    chat_id = update.message.chat.id
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        await update.message.chat.send_action(action=ChatAction.TYPING)
        
        try:
            user_id = f"{chat_id}_{update.message.message_id}"
            local_answer = get_local_answer(user_message, user_id)
            
            if local_answer and local_answer != "اسأل 'ش تدرس' أو 'شكد عمرج' علشان افهم سؤالك":
                ai_response = local_answer
            elif local_answer and "اسأل" in local_answer:
                ai_response = local_answer
            else:
                # استخدام Gemini AI
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
                prompt = f"أجب بإجابة مختصرة باللهجة العراقية: {user_message}"
                
                response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
                
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
        
        # التحقق إذا كان رداً على أي رسالة للبوت
        is_reply_to_bot = False
        if reply_to and reply_to.from_user and reply_to.from_user.id == context.bot.id:
            if chat_id in bot_messages and reply_to.message_id in bot_messages[chat_id]:
                is_reply_to_bot = True
        
        # التحقق إذا كان مناداة مباشرة
        is_mention = any(keyword in user_message.lower() for keyword in ["قمر", "@userhak_bot"])
        
        # إذا كان رداً على البوت أو مناداة مباشرة
        if is_reply_to_bot or is_mention:
            await update.message.chat.send_action(action=ChatAction.TYPING)
            asyncio.create_task(handle_ai_response(user_message, update.message.message_id, chat_id, context))

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        if chat_id in active_groups and active_groups[chat_id]:
            await update.message.reply_text("⚠️ البوت مشغل بالفعل!")
            return
        
        # إيقاف أي مهمة سابقة
        if chat_id in group_tasks:
            group_tasks[chat_id].cancel()
        
        # تفعيل المجموعة
        active_groups[chat_id] = True
        bot_messages[chat_id] = []
        
        # إرسال أول رسالة فوراً
        phrase = random.choice(IRAQI_PHRASES)
        message = await context.bot.send_message(chat_id=chat_id, text=phrase)
        bot_messages[chat_id].append(message.message_id)
        
        # بدء المهمة التلقائية
        task = asyncio.create_task(send_group_message(chat_id, context))
        group_tasks[chat_id] = task
        
        await update.message.reply_text("✅ تم تشغيل البوت قمر!")
        logger.info(f"🚀 تم التشغيل في {chat_id}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        if chat_id not in active_groups or not active_groups[chat_id]:
            await update.message.reply_text("⚠️ البوت غير مشغل!")
            return
        
        # إيقاف المهمة
        if chat_id in group_tasks:
            group_tasks[chat_id].cancel()
            del group_tasks[chat_id]
        
        if chat_id in active_groups:
            del active_groups[chat_id]
        
        if chat_id in bot_messages:
            del bot_messages[chat_id]
        
        await update.message.reply_text("⏹️ تم إيقاف البوت!")
        
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ")

def main():
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", start_bot))
        application.add_handler(CommandHandler("startbot", start_bot))
        application.add_handler(CommandHandler("stopbot", stop_bot))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
        
        # تعيين الأوامر
        application.post_init = lambda app: set_bot_commands(app)
        
        logger.info("🚀 البوت قمر يعمل...")
        logger.info(f"💾 النظام المحلي جاهز: {len(SIMPLE_QA)} سؤال")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()