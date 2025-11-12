import asyncio
import json
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from datetime import datetime

CONFIG_FILE = 'user_config.json'

target_user = None
forward_to = None

def load_config():
    """بارگذاری تنظیمات از فایل"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_config(config):
    """ذخیره تنظیمات در فایل"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_user_input():
    """دریافت اطلاعات از کاربر با اعتبارسنجی"""
    print("\n" + "="*50)
    print("🤖 خوش آمدید به ربات مانیتور تلگرام")
    print("="*50 + "\n")

    print("📝 لطفاً اطلاعات خود را وارد کنید:\n")

    # دریافت و اعتبارسنجی API ID
    while True:
        api_id = input("🔑 API ID خود را وارد کنید: ").strip()
        if api_id.isdigit() and len(api_id) > 0:
            api_id = int(api_id)
            break
        else:
            print("❌ API ID باید یک عدد باشد. دوباره تلاش کنید.\n")

    # دریافت و اعتبارسنجی API HASH
    while True:
        api_hash = input("🔐 API HASH خود را وارد کنید: ").strip()
        if len(api_hash) > 0:
            break
        else:
            print("❌ API HASH نمی‌تواند خالی باشد. دوباره تلاش کنید.\n")

    # دریافت و اعتبارسنجی شماره تلفن
    while True:
        phone = input("📱 شماره همراه خود را با +98 وارد کنید (مثال: +989123456789): ").strip()
        if len(phone) > 0:
            if not phone.startswith('+98'):
                if phone.startswith('98'):
                    phone = '+' + phone
                elif phone.startswith('0'):
                    phone = '+98' + phone[1:]
                else:
                    phone = '+98' + phone
            break
        else:
            print("❌ شماره تلفن نمی‌تواند خالی باشد. دوباره تلاش کنید.\n")

    # دریافت و اعتبارسنجی توکن ربات
    while True:
        bot_token = input("🤖 توکن ربات تلگرام خود را وارد کنید: ").strip()
        if len(bot_token) > 0:
            break
        else:
            print("❌ توکن ربات نمی‌تواند خالی باشد. دوباره تلاش کنید.\n")

    return {
        'api_id': api_id,
        'api_hash': api_hash,
        'phone': phone,
        'bot_token': bot_token,
        'session': ''
    }

# --------------------- توابع جدید برای قابلیت شمارش ---------------------

async def get_group_dialogs(user_client):
    """
    لیستی از گروه‌ها/سوپرگروه‌ها بازمی‌گرداند که کاربر (user_client) عضوشان است.
    خروجی: [{'id': dialog.entity.id, 'title': dialog.name}, ...]
    """
    groups = []
    async for dialog in user_client.iter_dialogs():
        # dialog.is_user, dialog.is_group, dialog.is_channel
        try:
            # سعی می‌کنیم گروه‌ها و سوپرگروه‌ها را انتخاب کنیم
            if dialog.is_group or getattr(dialog.entity, 'megagroup', False):
                title = dialog.name or getattr(dialog.entity, 'title', str(dialog.entity.id))
                groups.append({'id': dialog.entity.id, 'title': title})
        except Exception:
            # نادیده گرفتن خطاهای غیرمنتظره روی بعضی دیالوگ‌ها
            continue
    return groups

async def count_daily_messages(user_client, target_user_id, group_id, limit_per_group=1000):
    """
    تعداد پیام‌های 'امروز' از target_user_id در یک گروه مشخص را می‌شمارد.
    limit_per_group: حداکثر تعداد پیام که بررسی می‌کنیم (برای جلوگیری از کندی).
    """
    count = 0
    # اگر پیام‌ها خیلی زیاد باشند، بررسی را پس از limit_per_group پیام متوقف می‌کنیم.
    i = 0
    async for msg in user_client.iter_messages(group_id, from_user=target_user_id):
        i += 1
        if i > limit_per_group:
            # توقف برای جلوگیری از اسکن بی‌نهایت
            break
        try:
            # msg.date معمولاً دارای timezone-aware هست؛ بنابراین تنها تاریخ را مقایسه می‌کنیم
            msg_date = msg.date
            today = datetime.now(msg_date.tzinfo).date() if msg_date.tzinfo else datetime.now().date()
            if msg_date.date() == today:
                count += 1
            else:
                # چون پیام‌ها به ترتیب زمانی هستند، اگر تاریخ قدیمی‌تر شد می‌تونیم خارج بشیم
                break
        except Exception:
            # اگر هر پیام مشکلی داشت، از اون بگذریم
            continue
    return count

# ---------------------------------------------------------------------

async def main():
    global target_user, forward_to

    # بررسی وجود تنظیمات
    config = load_config()

    if config is None:
        print("\n⚙️  اولین بار است که ربات را اجرا می‌کنید\n")
        config = get_user_input()
        save_config(config)
    else:
        print("\n✅ تنظیمات قبلی شما پیدا شد!")
        print(f"📱 شماره: {config['phone']}")

        use_saved = input("\n❓ آیا می‌خواهید از تنظیمات قبلی استفاده کنید؟ (y/n): ").strip().lower()

        if use_saved not in ['y', 'yes', 'بله', 'ب']:
            print("\n🔄 دریافت تنظیمات جدید...\n")
            config = get_user_input()
            save_config(config)

    print("\n" + "="*50)
    print("🚀 در حال اتصال به تلگرام...")
    print("="*50 + "\n")

    # ایجاد کلاینت‌ها
    user_client = TelegramClient(
        StringSession(config.get('session', '')),
        config['api_id'],
        config['api_hash']
    )

    bot_client = TelegramClient(
        'bot_session',
        config['api_id'],
        config['api_hash']
    )

    # اتصال به تلگرام
    await bot_client.start(bot_token=config['bot_token'])
    print("✅ ربات متصل شد")

    await user_client.start(phone=config['phone'])
    print("✅ اکانت کاربری متصل شد")

    # ذخیره session برای دفعات بعد
    session_string = user_client.session.save()
    if session_string != config.get('session', ''):
        config['session'] = session_string
        save_config(config)
        print("💾 Session ذخیره شد")

    print("\n" + "="*50)
    print("✅ هر دو اکانت با موفقیت متصل شدند!")
    print("="*50 + "\n")

    # تعریف دستورات ربات
    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_command(event):
        welcome_msg = """
🤖 خوش آمدید به ربات مانیتور تلگرام!

📋 دستورات موجود:
/settarget [USER_ID] - تنظیم کاربر هدف برای مانیتور
/setforward [CHAT_ID] - تنظیم مقصد فوروارد پیام‌ها
/sta - نمایش لیست اکانت‌های مانیتور شده
/status - بررسی وضعیت ربات
/dailyreport - گزارش تعداد پیام‌های امروز در گروه‌های مشترک
/help - نمایش راهنما

💡 برای شروع، ابتدا کاربر هدف و مقصد فوروارد را تنظیم کنید.
        """
        await event.reply(welcome_msg)

    @bot_client.on(events.NewMessage(pattern='/help'))
    async def help_command(event):
        help_msg = """
📚 راهنمای استفاده از ربات:

1️⃣ /settarget [USER_ID]
   تنظیم ID کاربری که می‌خواهید پیام‌هایش را مانیتور کنید
   مثال: /settarget 123456789

2️⃣ /setforward [CHAT_ID]
   تنظیم ID چت یا کانالی که پیام‌ها به آن فوروارد شوند
   مثال: /setforward -1001234567890

3️⃣ /sta
   نمایش لیست کاربران و چت‌های تنظیم شده

4️⃣ /status
   بررسی وضعیت فعال بودن ربات

5️⃣ /dailyreport
   دریافت گزارش تعداد پیام‌های امروز کاربر هدف در گروه‌های مشترک

❓ نکته: برای پیدا کردن USER_ID یا CHAT_ID می‌توانید از ربات‌های مخصوص تلگرام استفاده کنید.
        """
        await event.reply(help_msg)

    @bot_client.on(events.NewMessage(pattern='/settarget (\\d+)'))
    async def set_target(event):
        global target_user
        target_user = int(event.pattern_match.group(1))
        await event.reply(f"✅ هدف تنظیم شد: {target_user}\n\n📥 از این پس پیام‌های این کاربر قابل مانیتور شدن هستند.")

    @bot_client.on(events.NewMessage(pattern='/setforward (-?\\d+)'))
    async def set_forward(event):
        global forward_to
        forward_to = int(event.pattern_match.group(1))
        await event.reply(f"✅ مقصد فوروارد تنظیم شد: {forward_to}\n\n📤 پیام‌ها به این مقصد فوروارد خواهند شد.")

    @bot_client.on(events.NewMessage(pattern='/sta'))
    async def show_targets(event):
        if target_user and forward_to:
            await event.reply(f"🎯 تنظیمات فعلی:\n\n📥 هدف: {target_user}\n📤 فوروارد به: {forward_to}\n\n✅ ربات فعال است و پیام‌ها را مانیتور می‌کند.")
        elif target_user:
            await event.reply(f"🎯 تنظیمات فعلی:\n\n📥 هدف: {target_user}\n📤 فوروارد به: ⚠️ تنظیم نشده\n\n⚠️ لطفاً با /setforward مقصد را تنظیم کنید.")
        elif forward_to:
            await event.reply(f"🎯 تنظیمات فعلی:\n\n📥 هدف: ⚠️ تنظیم نشده\n📤 فوروارد به: {forward_to}\n\n⚠️ لطفاً با /settarget کاربر هدف را تنظیم کنید.")
        else:
            await event.reply("❌ هیچ اکانتی تنظیم نشده است\n\nلطفاً ابتدا با دستورات زیر تنظیمات را انجام دهید:\n/settarget [USER_ID]\n/setforward [CHAT_ID]")

    @bot_client.on(events.NewMessage(pattern='/status'))
    async def show_status(event):
        status_msg = "✅ ربات روشن است و در حال کار می‌باشد\n\n"
        if target_user and forward_to:
            status_msg += "🟢 مانیتورینگ فعال است"
        elif target_user or forward_to:
            status_msg += "🟡 تنظیمات ناقص است - لطفاً هم هدف و هم مقصد را تنظیم کنید"
        else:
            status_msg += "🔴 تنظیمات انجام نشده - از /help استفاده کنید"

        await event.reply(status_msg)

    # دستور جدید: شمارش پیام‌های روزانه در گروه‌های مشترک
    @bot_client.on(events.NewMessage(pattern='/dailyreport'))
    async def daily_report(event):
        if not target_user:
            await event.reply("❌ ابتدا باید با دستور /settarget کاربر هدف را مشخص کنید.")
            return

        await event.reply("⏳ در حال بررسی گروه‌های مشترک و شمارش پیام‌ها... (ممکن است چند ثانیه طول بکشد)")

        try:
            groups = await get_group_dialogs(user_client)
            if not groups:
                await event.reply("⚠️ هیچ گروهی در حساب کاربری پیدا نشد.")
                return

            report_lines = []
            total = 0
            # اگر تعداد گروه‌ها خیلی زیاد بود می‌تونی اینجا محدود کنی (مثلاً groups[:50])
            for g in groups:
                count = await count_daily_messages(user_client, target_user, g['id'], limit_per_group=1000)
                total += count
                report_lines.append(f"💬 {g['title']}: {count} پیام")

            if not report_lines:
                await event.reply("⚠️ هیچ گروه مشترکی برای بررسی پیدا نشد.")
                return

            report_text = f"📊 گزارش فعالیت امروز کاربر {target_user}:\n\n" + "\n".join(report_lines)
            report_text += f"\n\n🕒 مجموع پیام‌ها امروز: {total}"

            # اگر پیام خیلی طولانی شد، آن را در چند پیام بفرست
            if len(report_text) > 4000:
                # قسمت‌بندی متن
                parts = [report_text[i:i+3500] for i in range(0, len(report_text), 3500)]
                for p in parts:
                    await event.reply(p)
            else:
                await event.reply(report_text)

        except Exception as e:
            await event.reply(f"❌ خطا در تولید گزارش: {e}")

    @user_client.on(events.NewMessage())
    async def monitor(event):
        if target_user and forward_to and event.sender_id == target_user:
            try:
                await event.message.forward_to(forward_to)
                print(f"✅ پیام فوروارد شد از {target_user} به {forward_to}")
            except Exception as e:
                print(f"❌ خطا در فوروارد پیام: {e}")

    print("🚀 ربات ۲۴/۷ فعال شد و منتظر پیام‌هاست!")
    print("💬 برای شروع، دستور /start را در ربات خود ارسال کنید.\n")

    # نگه داشتن ربات در حالت اجرا
    await asyncio.sleep(float('inf'))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 ربات متوقف شد. خدانگهدار!")
    except Exception as e:
        print(f"\n❌ خطا رخ داد: {e}")
