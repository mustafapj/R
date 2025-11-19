#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 بدء تشغيل مشروع DeepSeek Bot..."
echo "📅 $(date)"

# الانتقال إلى مجلد المشروع
cd /home/storage/shared/deepseek_bot

# تشغيل Tor
echo "🔒 تشغيل Tor..."
tor &
sleep 10

# التحقق من تثبيت المتطلبات
echo "📦 التحقق من المتطلبات..."
pip install -r requirements.txt

# تشغيل البوت
echo "🤖 تشغيل البوت الرئيسي..."
python bot.py