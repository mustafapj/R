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
ADMIN_USERNAME = "@pw19k"

# تخزين البيانات
active_groups = {}
group_tasks = {}
current_phrases = {}
admin_chat_id = None

async def send_to_admin(context, message):
    """إرسال رسالة إلى الأدمن"""
    global admin_chat_id
    
    try:
        if admin_chat_id is None:
            # محاولة الحصول على chat_id من خلال إرسال رسالة
            sent_message = await context.bot.send_message(
                chat_id=ADMIN_USERNAME,
                text="🔔 البوت يعمل الآن وجاهز لاستقبال التقارير!"
            )
            admin_chat_id = sent_message.chat_id
            logger.info(f"✅ تم تحديد chat_id للأدمن: {admin_chat_id}")
        else:
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=message
            )
            logger.info(f"📤 تم إرسال رسالة إلى الأدمن")
            
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال للأدمن: {e}")
        # إذا فشل الإرسال، نعرض الرسالة في الترمكس بدلاً من ذلك
        print(f"📝 [رسالة للأدمن]: {message}")

async def get_group_info(chat_id, context):
    """الحصول على معلومات المجموعة"""
    try:
        chat = await context.bot.get_chat(chat_id)
        members_count = await context.bot.get_chat_members_count(chat_id)
        
        info_message = f"""
📊 **معلومات مجموعة جديدة:**

🏷️ **اسم المجموعة:** {chat.title}
👥 **عدد الأعضاء:** {members_count}
🆔 **معرف المجموعة:** {chat_id}
📅 **تم الإنشاء:** {chat.date.strftime('%Y-%m-%d %H:%M') if chat.date else 'غير معروف'}
        """
        
        await send_to_admin(context, info_message)
        
    except Exception as e:
        logger.error(f"❌ خطأ في جلب معلومات المجموعة: {e}")
        error_msg = f"❌ خطأ في جلب معلومات المجموعة {chat_id}: {e}"
        await send_to_admin(context, error_msg)

async def log_user_info(update, context):
    """تسجيل معلومات المستخدم"""
    try:
        user = update.message.from_user
        user_name = f"{user.first_name} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "لا يوجد يوزر"
        chat_type = "خاص" if update.message.chat.type == "private" else "مجموعة"
        
        user_message = f"""
👤 **مستخدم جديد:**

📛 **الاسم:** {user_name}
🎯 **اليوزر:** {username}
🆔 **الآيدي:** {user.id}
💬 **نوع المحادثة:** {chat_type}
📝 **الرسالة:** {update.message.text[:100]}{'...' if len(update.message.text) > 100 else ''}
        """
        
        await send_to_admin(context, user_message)
        
    except Exception as e:
        logger.error(f"❌ خطأ في تسجيل معلومات المستخدم: {e}")

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
    
    # تسجيل معلومات المستخدم
    await log_user_info(update, context)
    
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
            
            logger.info(f"✅ تم التعرف على رد صحيح في المجموعة")
            
            await update.message.chat.send_action(action=ChatAction.TYPING)
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
                
                prompt = f"أجب بإجابة مختصرة جداً (جملة واحدة) باللهجة العراقية: {user_message}"
                
                response = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    full_response = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # تقصير الرد
                    if len(full_response) > 80:
                        sentences = full_response.split('.')
                        ai_response = '.'.join(sentences[:1]) + '.'
                    else:
                        ai_response = full_response
                    
                    # إرسال الرد بدون ذكر الاسم
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=ai_response,
                        reply_to_message_id=update.message.message_id
                    )
                    logger.info(f"✅ تم الرد في المجموعة")
                    
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ معليش، ما قدرت أرد هسه",
                        reply_to_message_id=update.message.message_id
                    )
                    
            except Exception as e:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ معليش، ما قدرت أرد هسه",
                    reply_to_message_id=update.message.message_id
                )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت في المحادثة الخاصة"""
    global admin_chat_id
    
    # تعيين الأدمن عند أول تفاعل
    if admin_chat_id is None:
        admin_chat_id = update.message.chat_id
        await send_to_admin(context, "✅ تم ربط البوت مع الأدمن بنجاح!")
    
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
        
        # إرسال معلومات المجموعة إلى الأدمن
        await get_group_info(chat_id, context)
        
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
        print("📊 إرسال معلومات المجموعات والمستخدمين إلى @pw19k")
        print("💬 يدعم المحادثات الخاصة والمجموعات")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()