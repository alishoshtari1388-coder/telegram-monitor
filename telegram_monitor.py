import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import json

API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
PHONE = os.environ.get('PHONE')

CONFIG_FILE = 'config.json'
SESSION_FILE = 'session.txt'

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

# درست کردن کلاینت کاربر با session ذخیره شده
if os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, 'r') as f:
        saved_session = f.read().strip()
    if saved_session:
        user_client = TelegramClient(StringSession(saved_session), API_ID, API_HASH)
    else:
        user_client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
else:
    user_client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

bot_client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def save_session():
    session_str = user_client.session.save()
    if session_str and not os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'w') as f:
            f.write(session_str)
        print(f"SESSION با موفقیت ذخیره شد: {session_str[:50]}...")

@bot_client.on(events.NewMessage(pattern='/settarget (\\d+)'))
async def set_target(event):
    global target
    target = int(event.pattern_match.group(1))
    config['target'] = target
    save_config(config)
    await event.reply(f"هدف: {target} ✅")

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
        await event.reply("❌ اول تارگت و فوروارد رو بزن!")
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
    txt = f"🎯 هدف: {target or 'نداره'}\n📩 مقصد: {forward_to or 'نداره'}\n⚡ وضعیت: {'فعال 🚀' if active else 'خاموش ⏹'}"
    await event.reply(txt)

@user_client.on(events.NewMessage)
async def handler(event):
    if active and target and forward_to and event.sender_id == target:
        try:
            await user_client.forward_messages(forward_to, event.message)
            print(f"فوروارد شد از {target}")
        except Exception as e:
            print(f"خطا: {e}")

async def main():
    print("در حال اتصال به تلگرام...")
    await user_client.start(phone=PHONE)
    await save_session()
    print("ربات ۲۴/۷ فعال شد | SESSION ذخیره شد | تا قیامت روشن! 🚀")
    await asyncio.sleep(999999999)

if __name__ == '__main__':
    asyncio.run(main())
