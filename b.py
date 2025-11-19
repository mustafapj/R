import requests
import random
import asyncio
import logging
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction

# استيراد الملفات
from phrases import IRAQI_PHRASES
from simple_qa import SIMPLE_QA
from config import TELEGRAM_TOKEN, GEMINI_API_KEY, CHANNEL_USERNAME, GROUP_LINK, CHANNEL_LINK, OWNER_USERNAME, BOT_NAME

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تخزين البيانات
active_groups = {}
group_tasks = {}
bot_messages = {}
user_status = {}  # تخزين حالة المستخدمين

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

async def check_subscription(user_id, context):
    """التحقق من اشتراك المستخدم في القناة والمجموعة"""
    try:
        # التحقق من القناة
        channel_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        channel_subscribed = channel_member.status in ['member', 'administrator', 'creator']
        
        # التحقق من المجموعة (باستخدام معرف المجموعة من الرابط)
        group_subscribed = False
        try:
            # استخراج معرف المجموعة من الرابط
            if "t.me/+" in GROUP_LINK:
                # إذا كان رابط دعوة
                group_invite = GROUP_LINK.split('/')[-1]
                group_member = await context.bot.get_chat_member(chat_id=group_invite, user_id=user_id)
                group_subscribed = group_member.status in ['member', 'administrator', 'creator']
            else:
                # إذا كان معرف عادي
                group_username = GROUP_LINK.split('/')[-1]
                if group_username.startswith('@'):
                    group_member = await context.bot.get_chat_member(chat_id=group_username, user_id=user_id)
                else:
                    group_member = await context.bot.get_chat_member(chat_id="@" + group_username, user_id=user_id)
                group_subscribed = group_member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من المجموعة: {e}")
            group_subscribed = False
        
        logger.info(f"📊 التحقق - القناة: {channel_subscribed}, المجموعة: {group_subscribed}")
        return channel_subscribed, group_subscribed
        
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من الاشتراك: {e}")
        return False, False

async def subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر التحقق من الاشتراك"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    # التحقق من الاشتراك
    channel_subscribed, group_subscribed = await check_subscription(user_id, context)
    
    if channel_subscribed and group_subscribed:
        # إذا مشترك في كليهما
        user_status[user_id] = True
        
        # إنشاء الأزرار الأربعة للرسالة الجديدة
        keyboard = [
            [InlineKeyboardButton("📢 قناتنا", url=CHANNEL_LINK),
             InlineKeyboardButton("👥 مجموعتنا", url=GROUP_LINK)],
            [InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"),
             InlineKeyboardButton("✅ تم التحقق", callback_data="already_verified")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"✅ تم التحقق بنجاح!\n"
            f"شكراً للاشتراك في قناتنا ومجموعتنا\n\n"
            f"💫 كيف يمكنني مساعدتك اليوم؟\n\n"
            f"يمكنك زيارة:\n"
            f"- قناتنا للأخبار والتحديثات\n"
            f"- مجموعتنا للتواصل مع الأعضاء\n"
            f"- المطور لأي استفسار تقني",
            reply_markup=reply_markup
        )
        
    else:
        # إذا غير مشترك في أحدهما أو كليهما
        missing = []
        if not channel_subscribed:
            missing.append(f"📢 القناة: {CHANNEL_LINK}")
        if not group_subscribed:
            missing.append(f"👥 المجموعة: {GROUP_LINK}")
        
        missing_text = "\n".join(missing)
        
        # إعادة إنشاء الأزرار الأربعة
        keyboard = [
            [InlineKeyboardButton("📢 قناتنا", url=CHANNEL_LINK),
             InlineKeyboardButton("👥 مجموعتنا", url=GROUP_LINK)],
            [InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"),
             InlineKeyboardButton("🔍 تحقق مرة أخرى", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"❌ لم يتم التحقق من الاشتراك\n\n"
            f"يجب الاشتراك في:\n{missing_text}\n\n"
            f"بعد الاشتراك، اضغط على زر التحقق:",
            reply_markup=reply_markup
        )

async def already_verified_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر 'تم التحقق'"""
    query = update.callback_query
    await query.answer("✅ أنت مفعل بالفعل!", show_alert=True)

def get_local_answer(user_message):
    """البحث في الإجابات المحلية أولاً"""
    user_message = user_message.strip().lower()
    
    # فقط إذا السؤال موجود في القائمة → إرجاع الإجابة
    if user_message in SIMPLE_QA:
        return SIMPLE_QA[user_message]
    
    # أي سؤال آخر → يرجع None لاستخدام الذكاء الاصطناعي
    return None

async def handle_ai_response(user_message, reply_to_message_id, chat_id, context):
    """معالجة الرد من الذكاء الاصطناعي"""
    try:
        # البحث في الإجابات المحلية أولاً
        local_answer = get_local_answer(user_message)
        
        if local_answer:
            ai_response = local_answer
            logger.info(f"✅ استخدام الإجابة المحلية: {ai_response}")
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
    user_id = update.message.from_user.id
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        # التحقق إذا كان المستخدم مفعل
        if user_id not in user_status or not user_status[user_id]:
            # إنشاء الأزرار الأربعة
            keyboard = [
                [InlineKeyboardButton("📢 قناتنا", url=CHANNEL_LINK),
                 InlineKeyboardButton("👥 مجموعتنا", url=GROUP_LINK)],
                [InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"),
                 InlineKeyboardButton("🔍 تحقق من الاشتراك", callback_data="check_subscription")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❗️ يجب التحقق من الاشتراك أولاً\n\n"
                f"اضغط على الزر أدناه للتحقق بعد الاشتراك:",
                reply_markup=reply_markup
            )
            return
        
        await update.message.chat.send_action(action=ChatAction.TYPING)
        
        try:
            local_answer = get_local_answer(user_message)
            
            if local_answer:
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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت مع الأزرار الأربعة"""
    user_id = update.message.from_user.id
    
    # إذا كانت محادثة خاصة
    if update.message.chat.type == "private":
        # إنشاء الأزرار الأربعة
        keyboard = [
            [InlineKeyboardButton("📢 قناتنا", url=CHANNEL_LINK),
             InlineKeyboardButton("👥 مجموعتنا", url=GROUP_LINK)],
            [InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"),
             InlineKeyboardButton("🔍 تحقق من الاشتراك", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"أهلاً بك! 👋\n"
            f"لاستخدام البوت، يجب الاشتراك في قناتنا ومجموعتنا\n\n"
            f"💫 يمكنك:\n"
            f"- زيارة قناتنا ومجموعتنا عبر الأزرار\n"
            f"- أو التحقق مباشرة من الاشتراك\n\n"
            f"بعد الاشتراك، اضغط على زر التحقق:",
            reply_markup=reply_markup
        )
    else:
        # في المجموعات - استخدام الأمر العادي
        await start_bot(update, context)

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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مساعدة"""
    # إنشاء الأزرار الأربعة في رسالة المساعدة
    keyboard = [
        [InlineKeyboardButton("📢 قناتنا", url=CHANNEL_LINK),
         InlineKeyboardButton("👥 مجموعتنا", url=GROUP_LINK)],
        [InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"),
         InlineKeyboardButton("🚀 بدء البوت", callback_data="start_bot_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🆘 كيفية استخدام البوت:\n\n"
        f"💫 في المجموعات:\n"
        f"- اكتب /startbot لتشغيل البوت\n"
        f"- ناديه بـ 'قمر' أو رد على رسائله\n\n"
        f"💫 في المحادثة الخاصة:\n"
        f"- اضغط /start ثم 'تحقق من الاشتراك'\n"
        f"- بعد التحقق يمكنك المحادثة\n\n"
        f"📞 المطور: {OWNER_USERNAME}",
        reply_markup=reply_markup
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حالة البوت"""
    chat_id = update.message.chat.id
    
    if chat_id in active_groups and active_groups[chat_id]:
        status = "🟢 مشغل"
        messages_count = len(bot_messages.get(chat_id, []))
    else:
        status = "🔴 متوقف"
        messages_count = 0
    
    await update.message.reply_text(f"""
    📊 حالة البوت:
    
    الحالة: {status}
    الرسائل المحفوظة: {messages_count}
    المجموعات النشطة: {len(active_groups)}
    المستخدمين المفعلين: {len(user_status)}
    
    💾 النظام المحلي:
    - الأسئلة: {len(SIMPLE_QA)}
    - القناة: {CHANNEL_USERNAME}
    """)

async def start_bot_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر بدء البوت من المساعدة"""
    query = update.callback_query
    await query.answer()
    await start_command(update, context)

def main():
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("startbot", start_bot))
        application.add_handler(CommandHandler("stopbot", stop_bot))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
        application.add_handler(CallbackQueryHandler(subscription_callback, pattern="check_subscription"))
        application.add_handler(CallbackQueryHandler(already_verified_callback, pattern="already_verified"))
        application.add_handler(CallbackQueryHandler(start_bot_help_callback, pattern="start_bot_help"))
        
        # تعيين الأوامر
        application.post_init = lambda app: set_bot_commands(app)
        
        logger.info("🚀 البوت قمر يعمل...")
        logger.info(f"💾 النظام المحلي جاهز: {len(SIMPLE_QA)} سؤال")
        logger.info(f"🔒 نظام الاشتراك مفعل مع الأزرار الأربعة")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()