import requests
import random
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# تفعيل التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8520375677:AAGcmKBcCOKsaLcHPHvbiBjSP-rmRU48cOY"
GEMINI_API_KEY = "AIzaSyDKTY7PaRhgKJI-CdZSnClFTQ_WvC6_KvY"
ADMIN_USERNAME = "@pw19k"  # اليوزر الخاص للإرسال

# القائمة العراقية الرائعة
iraqi_phrases = [
    "هلو شباب، اكو واحد قاعد؟ وين طامسين؟",
    "صباح الخير شلونكم؟ شهدكم بالخاص لو بعدكم؟",
    "معودية مضايجه… اريد واحد يجي يصرفلي.",
    "اني ضايج اليوم، اذا اكو واحد قاعد يحجي وياي.",
    "وين طامسين يا جماعه؟ صارلي ساعه انادي!",
    "هسه منو قاعد؟ اريد سوالف، طفگت بعد.",
    "اكو واحد فاضي هسه؟ تعالوا صرفولي.",
    "صباح الورد يا حلوين، شخباركم اليوم؟",
    "هلو بنات، وين مختفيات؟ لا تطامسون.",
    "يمّه الجو ضايج، اكو احد يونسني؟",
    "وينكم؟ شهدكم بالخاص لو شنو؟ ردّولي.",
    "يا جماعة الخير، اريد سوالف… منو قاعد؟",
    "انتو طامسين لو شنو؟ اريد اسمع صوت!",
    "مساء الخير شلونكم؟ منو فاضي يصرفلي؟",
    "هلووو، احنا هنا لو بس آني قاعد؟",
    "صارلنا هواي بلا سوالف… يابه وينكم؟",
    "اشتاقيت لسوالفكم… منو قاعد هسه؟",
    "يابه اكو احد قاعد؟ خلي يسولف وياي.",
    "ها حبايب، وين طامسين؟ اريد سوالف.",
    "صباحكم خير ومحبه… منو قاعد يحچي وياي؟",
    "هلو جماعة، شهدكم بالخاص لو الدنيا زاحمتكم؟",
    "معودية مضايجه اليوم، فد واحد يونسني.",
    "وين أهل القعدة؟ اكو احد ولا طامسين؟",
    "أدري بيكم موجودين بس محد يرد.",
    "شصار عليكم؟ يومية طامسين!",
    "يلا قوموا، منو قاعد يحچي ويانا؟",
    "هلو حبايب، اريد واحد يصرفلي فد سوالف.",
    "وينكم؟ الدنيا فاضية بدون سوالفكم.",
    "اني محتاج سوالف… منو قاعد؟",
    "صباح الخير يطيبين، شخباركم اليوم؟",
    "وين طامسين؟ صارلي يوم كامل ما سامع صوتكم.",
    "شهدكم بالخاص لو تحبون تهملوني؟ ههه",
    "اريد سوالف تضحك… منو قاعد؟",
    "يابه حياتي ضايجة… اريد واحد يسولف.",
    "ها شباب وينكم؟ لو كلكم نايمين؟",
    "اكو أحد قاعد يريد يحچي؟",
    "مسّاكم الله بالخير… اكو قعدة لو لا؟",
    "وين سوالفكم؟ ماكو ولا واحد؟",
    "اني هنا… منو بعد؟",
    "شهدكم بالخاص لو تحضرون بس ما تحچون؟",
    "هلو… طامسين لو شنو؟",
    "اريد سوالفكم اليوم، لا حد يغيب.",
    "هلا بالحلوين… منو قاعد؟",
    "شلونكم؟ ليش هيج ساكتين؟",
    "يابه احجون… تكسر الخاطر الوحده.",
    "معودية مضايجه، اريد واحد يونسني شويه.",
    "منو يريد يحچي ويانا هسه؟",
    "صباح الورد شنو اخباركم؟",
    "وين طامسين؟ هسه هيج فجأة؟",
    "شجابكم؟ منو قاعد؟",
    "ها حبايب شنو الوضع؟",
    "اكو احد يريد يصرف؟ تعالوا.",
    "هلو صارت قعدة؟ لو بعد؟",
    "شهدكم بالخاص؟ وينكم؟",
    "اني ضايج… ساعدوني بسوالفكم.",
    "معودية اليوم مكعدتني… اريد سوالف.",
    "وين اهل الدوامه؟ اكو احد؟",
    "صباح الخير، شنو ناوين اليوم؟",
    "منو يريد يتونس ويانا هسه؟",
    "هلو يالغالين، وين طامسين؟",
    "شلونكم بعد؟ اكو احد؟",
    "وين راحت سوالفكم؟",
    "هسه يلا صحّوا؟ تعالوا.",
    "يابه منو يريد يحچي؟",
    "مساء الخير، وين طامسين؟",
    "ليش ساكتين؟ اكعدوا.",
    "اكو احد؟ لو بس آني؟",
    "وينكم طالعين؟",
    "يلا تعالوا سوالف.",
    "احجيولي شكو ماكو.",
    "صباح النور… منو موجود؟",
    "هلو حبايب، ليش طامسين؟",
    "اريد سوالف اليوم، منو قاعد؟",
    "وين جماعتنا؟",
    "ها وينكم؟ ماكو صوت.",
    "اكو واحد؟ ردوا.",
    "تعالوا خلي نصرف.",
    "هسه شنو؟ وين الكل؟",
    "اني مشتاق للسوالف.",
    "ها تريدون قعدة؟",
    "وين راحت سوالف امبارح؟",
    "شهدكم بالخاص؟",
    "صباح الخير عيني… شخباركم؟",
    "معودية من الصبح… اريد واحد يونسني.",
    "وينكم؟ لا تختفون.",
    "هلو شنو جديدكم؟",
    "منو يريد يحچي؟",
    "يابه ردوا عليّ.",
    "اكو احد قاعد لو لا؟",
    "وين طامسين؟ صار هواي.",
    "مساء الورد، شنو اخباركم؟",
    "هسه اجوي الغايبين؟",
    "ها شنو؟ ليش ساكتين؟",
    "تعالوا سولفوا، الوقت ضايج.",
    "اني هنا… وينكم؟",
    "شهدكم بالخاص؟ ردولي.",
    "زين منو يقعد وية؟",
    "اكو احد يريد يتونس؟",
    "صباح الورد… لا تختفون بعد.",
    "ايامكم سعيدة… منو قاعد؟",
    "تعالوا خلي نسولف شويه.",
    "وين طامسين يا جماعه الخير؟"
]

# تخزين البيانات
active_groups = {}
group_tasks = {}
current_phrases = {}

async def send_to_admin(context, message):
    """إرسال رسالة إلى الأدمن"""
    try:
        await context.bot.send_message(
            chat_id=ADMIN_USERNAME,
            text=message
        )
        logger.info(f"📤 تم إرسال رسالة إلى الأدمن")
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال للأدمن: {e}")

async def get_group_info(chat_id, context):
    """الحصول على معلومات المجموعة"""
    try:
        chat = await context.bot.get_chat(chat_id)
        members_count = await context.bot.get_chat_members_count(chat_id)
        
        # الحصول على المالك
        admins = await context.bot.get_chat_administrators(chat_id)
        owner = None
        admin_list = []
        
        for admin in admins:
            if admin.status == "creator":
                owner = admin.user
            else:
                admin_list.append(admin.user)
        
        owner_name = f"{owner.first_name} {owner.last_name or ''}".strip()
        owner_username = f"@{owner.username}" if owner.username else "لا يوجد يوزر"
        
        admin_names = []
        for admin in admin_list[:5]:  # أول 5 مشرفين فقط
            name = f"{admin.first_name} {admin.last_name or ''}".strip()
            username = f"@{admin.username}" if admin.username else "لا يوجد يوزر"
            admin_names.append(f"{name} ({username})")
        
        info_message = f"""
📊 **معلومات مجموعة جديدة:**

🏷️ **اسم المجموعة:** {chat.title}
👥 **عدد الأعضاء:** {members_count}
🆔 **معرف المجموعة:** {chat_id}
👑 **المالك:** {owner_name} ({owner_username})

🛡️ **المشرفين:**
{chr(10).join(admin_names) if admin_names else 'لا يوجد مشرفين آخرين'}
        """
        
        await send_to_admin(context, info_message)
        
    except Exception as e:
        logger.error(f"❌ خطأ في جلب معلومات المجموعة: {e}")

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
            # اختيار عبارة عشوائية
            if chat_id not in current_phrases:
                current_phrases[chat_id] = random.choice(iraqi_phrases)
            else:
                # تغيير العبارة كل مرة
                current_phrases[chat_id] = random.choice(iraqi_phrases)
            
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=current_phrases[chat_id]
            )
            
            # حفظ آخر رسالة للبوت
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
                timeout=10  # وقت أقل للاستجابة السريعة
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
                    timeout=10  # وقت أقل للاستجابة السريعة
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
        current_phrases[chat_id] = random.choice(iraqi_phrases)
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
        print("🎯 100 عبارة عراقية - تتغير كل 3 دقائق")
        print("⚡ ردود سريعة بدون أسماء")
        print("📊 إرسال معلومات المجموعات والمستخدمين إلى @pw19k")
        print("💬 يدعم المحادثات الخاصة والمجموعات")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()