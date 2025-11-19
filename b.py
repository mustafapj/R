import requests
import random
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

# استيراد العبارات من ملف منفصل
from phrases import IRAQI_PHRASES

# باقي الكود يبقى كما هو لكن أنظف
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
    # ... (نفس الدالة)

async def get_group_info(chat_id, context):
    """الحصول على معلومات المجموعة"""
    # ... (نفس الدالة)

async def log_user_info(update, context):
    """تسجيل معلومات المستخدم"""
    # ... (نفس الدالة)

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
            await asyncio.sleep(180)
            
    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الرسالة: {e}")

# باقي الدوال تبقى كما هي...
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (نفس الكود)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (نفس الكود)

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (نفس الكود)

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (نفس الكود)

def main():
    # ... (نفس الكود)

if __name__ == "__main__":
    main()