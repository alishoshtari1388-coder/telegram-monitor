import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import json

# تنظیمات محیطی
API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
PHONE = os.environ.get('PHONE')
SESSION_STRING = os.environ.get('SESSION_STRING', '').strip()

CONFIG_FILE = 'config.json'
SESSION_FILE = 'session.txt'

# بارگذاری تنظیمات
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"target": None, "forward_to": None, "active": False}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

config = load_config()
target = config.get("target")
forward_to = config.get("forward_to")
active = config.get("active", False)

# ساخت کلاینت کاربر — فقط یک بار!
if SESSION_STRING:
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    print("از SESSION_STRING لاگین شد (ضدبلاک و بدون کد) ✅")
elif os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, 'r') as f:
        saved = f.read().strip()
    if saved:
        user_client = TelegramClient(StringSession(saved), API_ID, API_HASH)
        print("از session.txt لاگین شد ✅")
    else:
        user_client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
else:
    user_client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

# کلاینت بات
bot_client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ذخیره session جدید (فقط اگه از فایل یا جدید باشه)
async def save_session():
    if not SESSION_STRING:  # فقط اگه از Secrets نباشه
        session_str = user_client.session.save()
        if session_str and not os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'w') as f:
                f.write(session_str)
            print(f"SESSION جدید ذخیره شد در session.txt: {session_str[:50]}...")

# دستورات بات
@bot_client.on(events.NewMessage(pattern='/settarget (\\d+)'))
async def set_target(event):
    global target
    target = int(event.pattern_match.group(1))
    config['target'] = target
    save_config(config)
    await event.reply(f"هدف تنظیم شد: {target} ✅")

@bot_client.on(events.NewMessage(pattern='/setforward (-?\\d+|@\\w+)'))
async def set_forward(event):
    global forward_to
    forward_to = event.pattern_match.group(1)
    config['forward_to'] = forward_to
    save_config(config)
    await event.reply(f"فوروارد به: {forward_to} ✅")

@bot_client.on(events.NewMessage(pattern='/startmonitor'))
async def start(event):
    global active
    if not target or not forward_to:
        await event.reply("❌ اول تارگت و فوروارد رو ست کن!")
        return
    active = True
    config['active'] = True
    save_config(config)
    await event.reply(f"مانیتورینگ شروع شد!\n{target} → {forward_to}\nهر پیام = فوروارد فوری! 🚀")

@bot_client.on(events.NewMessage(pattern='/stopmonitor'))
async def stop(event):
    global active
    active = False
    config['active'] = False
    save_config(config)
    await event.reply("متوقف شد ⏹")

@bot_client.on(events.NewMessage(pattern='/status'))
async def status(event):
    txt = f"🎯 هدف: {target or 'تنظیم نشده'}\n📩 مقصد: {forward_to or 'تنظیم نشده'}\n⚡ وضعیت: {'فعال 🚀' if active else 'خاموش ⏹'}"
    await event.reply(txt)

# مانیتورینگ پیام‌ها
@user_client.on(events.NewMessage)
async def handler(event):
    if active and target and forward_to and event.sender_id == target:
        try:
            await user_client.forward_messages(forward_to, event.message)
            print(f"پیام فوروارد شد از {target} به {forward_to}")
        except Exception as e:
            print(f"خطا در فوروارد: {e}")

# اجرای اصلی
async def main():
    print("در حال اتصال به تلگرام...")
    await user_client.start(phone=PHONE if not SESSION_STRING else None)
    await save_session()
    print("ربات ۲۴/۷ فعال شد | تا قیامت روشن! 🚀🔥")
    await asyncio.sleep(999999999)

if __name__ == '__main__':
    asyncio.run(main())
