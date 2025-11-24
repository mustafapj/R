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
from config import *

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== الدوال المساعدة ==========
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

def is_developer(user_id):
    """التحقق إذا كان المستخدم هو المطور"""
    return user_id == DEVELOPER_ID

def get_developer_info():
    """معلومات المطور"""
    return f"👨‍💻 المطور: {DEVELOPER_NAME}\n📞 الحساب: {DEVELOPER_USERNAME}"

async def check_subscription(user_id, context):
    """التحقق من اشتراك المستخدم في القناة فقط"""
    try:
        # التحقق من القناة فقط
        channel_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        channel_subscribed = channel_member.status in ['member', 'administrator', 'creator']
        
        # لم نعد نتحقق من المجموعة
        group_subscribed = True
        
        logger.info(f"📊 التحقق - القناة: {channel_subscribed}")
        return channel_subscribed, group_subscribed
        
    except Exception as e:
        logger.error(f"❌ خطأ في التحقق من الاشتراك: {e}")
        return False, True  # نعتبره مشترك في المجموعة

def get_local_answer(user_message):
    """البحث في الإجابات المحلية"""
    return SIMPLE_QA.get(user_message.strip().lower())

def create_main_keyboard():
    """إنشاء الأزرار الرئيسية"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 قناتنا", url=CHANNEL_LINK),
         InlineKeyboardButton("👥 مجموعتنا", url=GROUP_LINK)],
        [InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@', '')}"),
         InlineKeyboardButton("🔍 تحقق من الاشتراك", callback_data="check_subscription")]
    ])

# ========== معالجات الأوامر ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت"""
    user_id = update.message.from_user.id
    
    # إذا كان المطور
    if is_developer(user_id):
        user_status[user_id] = True
        await update.message.reply_text(
            f"🎉 أهلاً مطوري العزيز! {DEVELOPER_NAME}\n\n"
            f"🛠️ نظام المطور مفعل\n"
            f"⚡ يمكنك استخدام /admin للتحكم\n"
            f"🔓 أنت معفي من التحقق"
        )
        return
        
    if update.message.chat.type == "private":
        await update.message.reply_text(
            f"أهلاً بك! 👋\nلاستخدام البوت، يجب الاشتراك في قناتنا:\n{CHANNEL_USERNAME}\n\n"
            f"بعد الاشتراك، اضغط على زر التحقق:",
            reply_markup=create_main_keyboard()
        )
    else:
        await start_bot(update, context)

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل البوت في المجموعة"""
    chat_id = update.message.chat.id
    try:
        if chat_id in active_groups and active_groups[chat_id]:
            await update.message.reply_text("⚠️ البوت مشغل بالفعل!")
            return
        
        active_groups[chat_id] = True
        bot_messages[chat_id] = []
        
        # إرسال أول رسالة
        phrase = random.choice(IRAQI_PHRASES)
        message = await context.bot.send_message(chat_id=chat_id, text=phrase)
        bot_messages[chat_id].append(message.message_id)
        
        # بدء المهمة التلقائية
        task = asyncio.create_task(send_group_message(chat_id, context))
        group_tasks[chat_id] = task
        
        await update.message.reply_text("✅ تم تشغيل البوت قمر!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)}")

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إيقاف البوت في المجموعة"""
    chat_id = update.message.chat.id
    try:
        if chat_id not in active_groups or not active_groups[chat_id]:
            await update.message.reply_text("⚠️ البوت غير مشغل!")
            return
        
        if chat_id in group_tasks:
            group_tasks[chat_id].cancel()
            del group_tasks[chat_id]
        
        del active_groups[chat_id]
        if chat_id in bot_messages:
            del bot_messages[chat_id]
        
        await update.message.reply_text("⏹️ تم إيقاف البوت!")
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مساعدة"""
    await update.message.reply_text(
        f"🆘 كيفية استخدام البوت:\n\n"
        f"💫 في المجموعات:\n- /startbot لتشغيل البوت\n- ناديه بـ 'قمر'\n\n"
        f"💫 في الخاص:\n- /start ثم التحقق من الاشتراك\n\n"
        f"📞 المطور: {DEVELOPER_USERNAME}",
        reply_markup=create_main_keyboard()
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حالة البوت"""
    chat_id = update.message.chat.id
    status = "🟢 مشغل" if chat_id in active_groups and active_groups[chat_id] else "🔴 متوقف"
    messages_count = len(bot_messages.get(chat_id, []))
    
    await update.message.reply_text(f"""
📊 حالة البوت:
الحالة: {status}
الرسائل: {messages_count}
المجموعات: {len(active_groups)}
المستخدمين: {len(user_status)}
الأسئلة: {len(SIMPLE_QA)}
""")

# ========== معالجات الردود ==========
async def subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر التحقق من الاشتراك"""
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        await query.answer()
    except:
        pass  # نتجاهل أخطاء answer
    
    # إذا كان المطور، لا يحتاج تحقق
    if is_developer(user_id):
        user_status[user_id] = True
        await query.message.reply_text(
            f"🎉 أهلاً مطوري! {DEVELOPER_NAME}\n"
            f"🔓 تم التفعيل تلقائياً\n"
            f"🛠️ يمكنك استخدام /admin"
        )
        return
    
    # التحقق من الاشتراك في القناة فقط
    channel_subscribed, _ = await check_subscription(user_id, context)
    
    if channel_subscribed:
        # إذا مشترك في القناة
        user_status[user_id] = True
        await query.message.reply_text(
            f"✅ تم التحقق بنجاح!\n"
            f"شكراً للاشتراك في قناتنا {CHANNEL_USERNAME}\n\n"
            f"💫 كيف يمكنني مساعدتك اليوم؟"
        )
    else:
        # إذا غير مشترك في القناة
        await query.message.reply_text(
            f"❌ يجب الاشتراك في قناتنا أولاً:\n"
            f"📢 {CHANNEL_LINK}\n\n"
            f"بعد الاشتراك، اضغط على زر التحقق مرة أخرى",
            reply_markup=create_main_keyboard()
        )

async def handle_ai_response(user_message, reply_to_message_id, chat_id, context):
    """معالجة الردود"""
    try:
        local_answer = get_local_answer(user_message)
        if local_answer:
            ai_response = local_answer
        else:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, json={"contents": [{"parts": [{"text": f"أجب بإجابة مختصرة باللهجة العراقية: {user_message}"}]}]}, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                full_response = response.json()['candidates'][0]['content']['parts'][0]['text']
                ai_response = '.'.join(full_response.split('.')[:1]) + '.' if len(full_response) > 100 else full_response
            else:
                ai_response = "😊 آسف، حاول مرة ثانية"
        
        message = await context.bot.send_message(chat_id=chat_id, text=ai_response, reply_to_message_id=reply_to_message_id)
        
        if chat_id not in bot_messages:
            bot_messages[chat_id] = []
        bot_messages[chat_id].append(message.message_id)
        
        if len(bot_messages[chat_id]) > MAX_MESSAGES:
            bot_messages[chat_id] = bot_messages[chat_id][-MAX_MESSAGES:]
            
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text="😊 آسف، حاول مرة ثانية", reply_to_message_id=reply_to_message_id)

async def send_group_message(chat_id, context):
    """إرسال رسائل تلقائية"""
    try:
        while chat_id in active_groups and active_groups[chat_id]:
            phrase = random.choice(IRAQI_PHRASES)
            message = await context.bot.send_message(chat_id=chat_id, text=phrase)
            
            if chat_id not in bot_messages:
                bot_messages[chat_id] = []
            bot_messages[chat_id].append(message.message_id)
            
            if len(bot_messages[chat_id]) > MAX_MESSAGES:
                bot_messages[chat_id] = bot_messages[chat_id][-MAX_MESSAGES:]
            
            await asyncio.sleep(random.randint(120, 180))
    except Exception as e:
        logger.error(f"خطأ في الرسائل التلقائية: {e}")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل"""
    if not update.message or not update.message.text:
        return
    
    user_message = update.message.text
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    
    # ⬇️ التحقق إذا كان المطور
    if is_developer(user_id):
        # رسالة ترحيب خاصة عندما يتكلم المطور لأول مرة
        if user_id not in user_status:
            user_status[user_id] = True
            await update.message.reply_text(
                f"🎉 أهلاً وسهلاً يا مطوري! {DEVELOPER_NAME}\n\n"
                f"🛠️ أنت معروف كمطور النظام\n"
                f"⚡ يمكنك استخدام الأوامر الخاصة\n"
                f"📊 /admin - للوحة التحكم\n"
                f"📈 /stats - للإحصائيات"
            )
        
        # أوامر خاصة للمطور
        if user_message.lower() in ["/admin", "مطور", "ادمن", "لوحة التحكم"]:
            await update.message.reply_text(
                f"🛠️ لوحة المطور - {DEVELOPER_NAME}\n\n"
                f"📊 الإحصائيات:\n"
                f"- المجموعات النشطة: {len(active_groups)}\n"
                f"- المستخدمين المفعلين: {len(user_status)}\n"
                f"- الأسئلة المحلية: {len(SIMPLE_QA)}\n\n"
                f"⚡ الأوامر:\n"
                f"- /stats : إحصائيات مفصلة\n"
                f"- /users : قائمة المستخدمين\n"
                f"- /restart : إعادة تشغيل"
            )
            return
        
        elif user_message.lower() == "/stats":
            total_messages = sum(len(msgs) for msgs in bot_messages.values())
            stats_text = f"""
📈 إحصائيات مفصلة - {DEVELOPER_NAME}

👥 المستخدمين:
- المفعلين: {len(user_status)}
- أول 5 مستخدمين: {list(user_status.keys())[:5]}

🏘️ المجموعات:
- النشطة: {len(active_groups)}
- المجموعات: {list(active_groups.keys())}

💾 النظام:
- الأسئلة المحلية: {len(SIMPLE_QA)}
- الرسائل المحفوظة: {total_messages}
- الذاكرة: {total_messages * 0.1:.1f} كيلوبايت
"""
            await update.message.reply_text(stats_text)
            return
            
        elif user_message.lower() == "/users":
            users_list = "\n".join([f"- {user_id}" for user_id in list(user_status.keys())[:10]])
            await update.message.reply_text(f"👥 آخر 10 مستخدمين:\n{users_list}")
            return
    
    # ⬇️ إعفاء المطور من التحقق
    if is_developer(user_id):
        user_status[user_id] = True
    
    if update.message.chat.type == "private":
        if user_id not in user_status or not user_status[user_id]:
            await update.message.reply_text("❗️ يجب التحقق من الاشتراك أولاً", reply_markup=create_main_keyboard())
            return
        
        try:
            await update.message.chat.send_action(action=ChatAction.TYPING)
        except Exception as e:
            logger.warning(f"⚠️ خطأ في send_action: {e}")
        
        try:
            local_answer = get_local_answer(user_message)
            if local_answer:
                ai_response = local_answer
            else:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key={GEMINI_API_KEY}"
                response = requests.post(url, json={"contents": [{"parts": [{"text": f"أجب بإجابة مختصرة باللهجة العراقية: {user_message}"}]}]}, timeout=10)
                ai_response = response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else "❌ حدث خطأ"
        except:
            ai_response = "⚠️ معليش، ما قدرت أرد هسه"
        
        await update.message.reply_text(ai_response)
    
    elif update.message.chat.type in ["group", "supergroup"]:
        reply_to = update.message.reply_to_message
        is_reply_to_bot = reply_to and reply_to.from_user and reply_to.from_user.id == context.bot.id and chat_id in bot_messages and reply_to.message_id in bot_messages[chat_id]
        is_mention = any(keyword in user_message.lower() for keyword in ["قمر", "@userhak_bot"])
        
        if is_reply_to_bot or is_mention:
            try:
                await update.message.chat.send_action(action=ChatAction.TYPING)
            except Exception as e:
                logger.warning(f"⚠️ خطأ في send_action: {e}")
            
            asyncio.create_task(handle_ai_response(user_message, update.message.message_id, chat_id, context))

# ========== التشغيل الرئيسي ==========
def main():
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("startbot", start_bot))
        application.add_handler(CommandHandler("stopbot", stop_bot))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
        application.add_handler(CallbackQueryHandler(subscription_callback, pattern="check_subscription"))
        
        application.post_init = lambda app: set_bot_commands(app)
        
        logger.info("🚀 البوت قمر يعمل...")
        logger.info(f"💾 النظام المحلي: {len(SIMPLE_QA)} سؤال")
        logger.info(f"👑 المطور: {DEVELOPER_NAME} ({DEVELOPER_ID})")
        logger.info("🔒 نظام الاشتراك: القناة فقط")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()