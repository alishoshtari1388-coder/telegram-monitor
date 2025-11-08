import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
PHONE = os.environ.get('PHONE')
SESSION_STRING = os.environ.get('SESSION', '')

target_user = None
forward_to = None

user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
bot_client = TelegramClient('bot', API_ID, API_HASH)

async def main():
    print("در حال اتصال به تلگرام...")
    await bot_client.start(bot_token=BOT_TOKEN)
    await user_client.start(phone=PHONE)
    print("هر دو اکانت متصل شدن ✅")

    @bot_client.on(events.NewMessage(pattern='/settarget (\\d+)'))
    async def set_target(event):
        global target_user
        target_user = int(event.pattern_match.group(1))
        await event.reply(f"هدف تنظیم شد: {target_user}")

    @bot_client.on(events.NewMessage(pattern='/setforward (-?\\d+)'))
    async def set_forward(event):
        global forward_to
        forward_to = int(event.pattern_match.group(1))
        await event.reply(f"فوروارد به: {forward_to}")

    @user_client.on(events.NewMessage())
    async def monitor(event):
        if target_user and forward_to and event.sender_id == target_user:
            await event.message.forward_to(forward_to)
            print(f"پیام فوروارد شد از {target_user} به {forward_to}")

    print("ربات ۲۴/۷ فعال شد و منتظر پیام‌هاست 🚀")
    await asyncio.sleep(float('inf'))

if __name__ == '__main__':
    asyncio.run(main())
