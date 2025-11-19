# commands.py - ملف أوامر البوت مع زر الأوامر

from telegram import Update, BotCommand
from telegram.ext import ContextTypes
import random
import asyncio
import logging
from phrases import IRAQI_PHRASES

# تفعيل التسجيل
logger = logging.getLogger(__name__)

# المتغيرات المشتركة
active_groups = {}
group_tasks = {}
bot_messages = {}

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت في المحادثة الخاصة"""
    await update.message.reply_text(
        "🤖 **أهلاً! أنا البوت قمر**\n\n"
        "✨ **الميزات:**\n"
        "• أرسل رسائل عراقية كل 2-3 دقائق\n"
        "• أرد على أي شخص يرد على رسائلي\n"
        "• أرد على المناداة: قمر أو @userhak_bot\n\n"
        "🚀 **للتشغيل في مجموعة:**\n"
        "1. أضفني للمجموعة\n"
        "2. اكتب: /startbot\n\n"
        "⏹️ **لإيقاف البوت:** /stopbot\n"
        "ℹ️ **للمساعدة:** /help"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض مساعدة البوت"""
    help_text = """
📋 **أوامر البوت قمر:**

💬 **الأوامر المتاحة:**
/start - بدء البوت
/help - المساعدة
/startbot - تشغيل في المجموعة  
/stopbot - إيقاف في المجموعة
/status - حالة البوت

🎯 **الميزات:**
• ١٠٠ عبارة عراقية متنوعة
• ردود ذكية وسريعة
• محادثات مستمرة بدون توقف
• يدعم عدة أشخاص في نفس الوقت

🔔 **طريقة الاستخدام:**
1. شغل البوت في المجموعة بـ /startbot
2. البوت سيرسل رسائل كل 2-3 دقائق
3. رد على أي رسالة للبوت وسأرد عليك
4. ناديني بـ "قمر" أو "@userhak_bot"
"""
    await update.message.reply_text(help_text)

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        # التحقق إذا كان البوت مشغل بالفعل
        if chat_id in active_groups and active_groups[chat_id]:
            await update.message.reply_text(
                "⚠️ **البوت قمر مشغل بالفعل في هذه المجموعة!**\n\n"
                "لإعادة التشغيل، أوقف البوت أولاً بـ /stopbot"
            )
            return
        
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
            "✅ **تم تشغيل البوت قمر بنجاح!**\n\n"
            "📢 سأرسل رسائل عراقية كل 2-3 دقائق\n"
            "💬 سأرد على أي شخص يرد على رسائلي\n"
            "🔔 سأرد على المناداة: قمر أو @userhak_bot\n\n"
            "⏹️ لإيقاف البوت: /stopbot\n"
            "ℹ️ للمساعدة: /help"
        )
        logger.info(f"🚀 تم تشغيل البوت في المجموعة {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        await update.message.reply_text(
            "❌ **حدث خطأ في تشغيل البوت!**\n\n"
            "تأكد أن:\n"
            "• البوت لديه صلاحية إرسال الرسائل\n"
            "• البوت مشغل في المجموعة\n"
            "• حاول مرة أخرى بعد قليل"
        )

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت في المجموعة"""
    chat_id = update.message.chat.id
    
    try:
        # التحقق إذا كان البوت مشغل
        if chat_id not in active_groups or not active_groups[chat_id]:
            await update.message.reply_text(
                "⚠️ **البوت قمر غير مشغل في هذه المجموعة!**\n\n"
                "للتشغيل، اكتب: /startbot"
            )
            return
        
        # إيقاف المهمة
        if chat_id in group_tasks:
            group_tasks[chat_id].cancel()
            del group_tasks[chat_id]
        
        if chat_id in active_groups:
            del active_groups[chat_id]
        
        if chat_id in bot_messages:
            del bot_messages[chat_id]
        
        await update.message.reply_text(
            "⏹️ **تم إيقاف البوت قمر بنجاح!**\n\n"
            "شكراً لاستخدامكم البوت قمر 🌙\n"
            "لإعادة التشغيل، اكتب: /startbot"
        )
        logger.info(f"⏹️ تم إيقاف البوت في المجموعة {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في إيقاف البوت: {e}")
        await update.message.reply_text("❌ حدث خطأ في إيقاف البوت")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض حالة البوت"""
    chat_id = update.message.chat.id
    
    if update.message.chat.type == "private":
        status_text = "🤖 **حالة البوت قمر:**\n\n• ✅ البوت يعمل\n• 💬 جاهز للاستخدام في المجموعات"
    else:
        if chat_id in active_groups and active_groups[chat_id]:
            # حساب عدد الرسائل المحفوظة
            msg_count = len(bot_messages.get(chat_id, []))
            status_text = f"✅ **البوت قمر نشط في هذه المجموعة**\n\n• 📢 يرسل رسائل كل 2-3 دقائق\n• 💬 يرد على الردود والمناداة\n• 📝 عدد الرسائل المحفوظة: {msg_count}"
        else:
            status_text = "⏹️ **البوت قمر متوقف في هذه المجموعة**\n\nللتشغيل، اكتب: /startbot"
    
    await update.message.reply_text(status_text)

async def send_group_message(chat_id, context):
    """إرسال رسالة إلى المجموعة كل 2-3 دقائق"""
    try:
        while chat_id in active_groups and active_groups[chat_id]:
            # استخدام العبارات من الملف المستقل
            phrase = random.choice(IRAQI_PHRASES)
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=phrase
            )
            
            # حفظ الرسالة في قائمة آخر رسائل البوت
            if chat_id not in bot_messages:
                bot_messages[chat_id] = []
            
            # ✅ التأكد من حفظ الرسالة الجديدة
            bot_messages[chat_id].append(message.message_id)
            
            # الاحتفاظ بآخر 10 رسائل فقط
            if len(bot_messages[chat_id]) > 10:
                bot_messages[chat_id] = bot_messages[chat_id][-10:]
            
            # ✅ تسجيل تفصيلي للتحقق
            logger.info(f"📤 تم إرسال رسالة إلى المجموعة {chat_id}")
            logger.info(f"🆔 معرف الرسالة: {message.message_id}")
            logger.info(f"📋 القائمة الحالية: {bot_messages[chat_id]}")
            
            # انتظر 2-3 دقائق عشوائياً
            await asyncio.sleep(random.randint(120, 180))
            
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")