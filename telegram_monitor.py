import asyncio
import os
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# تنظیمات محیطی
API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
PHONE = os.environ.get('PHONE')
SESSION_STRING = os.environ.get('SESSION_STRING', '').strip()  # مهم: اسم درست SESSION_STRING

CONFIG_FILE = 'config.json'

# بارگذاری تنظیمات
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"targets": [], "forward_to": None, "monitoring": False}
    return {"targets": [], "forward_to": None, "monitoring": False}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

config = load_config()
targets = config.get("targets", [])           # لیست آیدی‌ها
forward_to = config.get("forward_to")
monitoring = config.get("monitoring", False)

# کلاینت‌ها
if SESSION_STRING:
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    print("از SESSION_STRING لاگین شد (ضدبلاک) ✅")
else:
    user_client = TelegramClient('user_session', API_ID, API_HASH)

bot_client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# دستورات ربات
@bot_client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(
        "ربات مانیتورینگ ۲۴/۷ آنلاینه!\n\n"
        "دستورات:\n"
        "/settarget 6768441111 → اضافه کردن هدف\n"
        "/setforward -1003198309189 → مقصد فوروارد\n"
        "/sta → لیست اهداف\n"
        "/status → وضعیت ربات\n"
        "/on → روشن کردن\n"
        "/off → خاموش کردن\n"
        "/clear → پاک کردن همه تنظیمات\n\n"
        "توسط علی خفن ساخته شد!"
    )

@bot_client.on(events.NewMessage(pattern='/settarget (\\d+)'))
async def set_target(event):
    global targets
    new_id = int(event.pattern_match.group(1))
    if new_id not in targets:
        targets.append(new_id)
        config['targets'] = targets
        save_config(config)
        await event.reply(f"هدف اضافه شد: {new_id} ✅\nکل اهداف: {len(targets)} تا")
    else:
        await event.reply(f"این هدف قبلاً اضافه شده!")

@bot_client.on(events.NewMessage(pattern='/setforward (-?\\d+)'))
async def set_forward(event):
    global forward_to
    forward_to = int(event.pattern_match.group(1))
    config['forward_to'] = forward_to
    save_config(config)
    await event.reply(f"مقصد فوروارد تنظیم شد: {forward_to} ✅")

@bot_client.on(events.NewMessage(pattern='/sta'))
async def list_targets(event):
    if not targets:
        await event.reply("هیچ هدفی تنظیم نشده!")
    else:
        txt = "لیست اهداف در حال مانیتور:\n"
        for i, t in enumerate(targets, 1):
            txt += f"{i}. `{t}`\n"
        txt += f"\nکل: {len(targets)} هدف"
        await event.reply(txt)

@bot_client.on(events.NewMessage(pattern='/status'))
async def status(event):
    status = "روشن 🚀" if monitoring else "خاموش ⏹"
    target_count = len(targets)
    dest = forward_to or "تنظیم نشده"
    await event.reply(
        f"وضعیت ربات:\n"
        f"مانیتورینگ: {status}\n"
        f"تعداد اهداف: {target_count}\n"
        f"مقصد: `{dest}`\n"
        f"تا قیامت روشن!"
    )

@bot_client.on(events.NewMessage(pattern='/on'))
async def turn_on(event):
    global monitoring
    if not targets or not forward_to:
        await event.reply("اول هدف و مقصد رو ست کن!")
        return
    monitoring = True
    config['monitoring'] = True
    save_config(config)
    await event.reply("مانیتورینگ روشن شد! 🚀")

@bot_client.on(events.NewMessage(pattern='/off'))
async def turn_off(event):
    global monitoring
    monitoring = False
    config['monitoring'] = False
    save_config(config)
    await event.reply("مانیتورینگ خاموش شد ⏹")

@bot_client.on(events.NewMessage(pattern='/clear'))
async def clear(event):
    global targets, forward_to, monitoring
    targets = []
    forward_to = None
    monitoring = False
    config = {"targets": [], "forward_to": None, "monitoring": False}
    save_config(config)
    if os.path.exists('config.json'):
        os.remove('config.json')
    await event.reply("همه تنظیمات پاک شد!")

# مانیتورینگ پیام‌ها
@user_client.on(events.NewMessage)
async def handler(event):
    if monitoring and forward_to and event.sender_id in targets:
        try:
            await user_client.forward_messages(forward_to, event.message)
            print(f"فوروارد شد از {event.sender_id} به {forward_to}")
        except Exception as e:
            print(f"خطا در فوروارد: {e}")

# اجرای اصلی
async def main():
    print("در حال اتصال به تلگرام...")
    await user_client.start(phone=PHONE if not SESSION_STRING else None)
    print("هر دو اکانت متصل شدن ✅")
    print("ربات ۲۴/۷ فعال شد و منتظر دستوراته 🚀")
    await asyncio.sleep(float('inf'))

if __name__ == '__main__':
    asyncio.run(main())
