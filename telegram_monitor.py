import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import KeyboardButtonCallback
from datetime import datetime
import logging
from config_manager import ConfigManager
from keep_alive import keep_alive

# فعال کردن keep_alive برای جلوگیری از خاموش شدن
keep_alive()

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# مدیر تنظیمات
config_manager = ConfigManager()

async def get_user_input():
    """دریافت اطلاعات از کاربر"""
    print("\n" + "=" * 50)
    print("لطفا اطلاعات خود را وارد کنید:")
    print("=" * 50 + "\n")

    # دریافت API ID
    while True:
        api_id = input("API ID خود را وارد کنید: ").strip()
        if api_id.isdigit() and len(api_id) > 0:
            api_id = int(api_id)
            break
        else:
            print("API ID باید یک عدد باشد.\n")

    # دریافت API HASH
    while True:
        api_hash = input("API HASH خود را وارد کنید: ").strip()
        if len(api_hash) > 0:
            break
        else:
            print("API HASH نمی تواند خالی باشد.\n")

    # دریافت شماره تلفن
    while True:
        phone = input("شماره همراه خود را وارد کنید (مثال: +989123456789): ").strip()
        if len(phone) > 0:
            if not phone.startswith('+'):
                if phone.startswith('98'):
                    phone = '+' + phone
                elif phone.startswith('0'):
                    phone = '+98' + phone[1:]
                else:
                    phone = '+98' + phone
            break
        else:
            print("شماره تلفن نمی تواند خالی باشد.\n")

    # دریافت توکن ربات
    while True:
        bot_token = input("توکن ربات تلگرام خود را وارد کنید: ").strip()
        if len(bot_token) > 0:
            break
        else:
            print("توکن ربات نمی تواند خالی باشد.\n")

    return {
        'api_id': api_id,
        'api_hash': api_hash,
        'phone': phone,
        'bot_token': bot_token,
        'session': ''
    }

async def get_all_groups(user_client):
    """دریافت لیست تمام گروه هایی که کاربر در آن است"""
    all_groups = []

    try:
        async for dialog in user_client.iter_dialogs():
            try:
                # فقط گروه ها و سوپرگروه ها
                if dialog.is_group or getattr(dialog.entity, 'megagroup', False):
                    group_id = dialog.entity.id
                    group_title = dialog.name or getattr(dialog.entity, 'title', 'Unknown')

                    all_groups.append({
                        'id': group_id,
                        'title': group_title
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"خطا در دریافت گروه ها: {e}")

    return all_groups

async def check_user_in_group(user_client, group_id, target_user_id):
    """بررسی اینکه کاربر در گروه خاصی هست یا نه"""
    try:
        async for message in user_client.iter_messages(
            group_id, 
            from_user=target_user_id,
            limit=1
        ):
            return True
    except Exception:
        pass

    try:
        permissions = await user_client.get_permissions(group_id, target_user_id)
        return permissions is not None
    except Exception:
        pass

    try:
        participants = await user_client.get_participants(group_id, limit=50)
        participant_ids = [p.id for p in participants]
        return target_user_id in participant_ids
    except Exception:
        pass

    return False

async def get_user_messages_in_group(user_client, target_user_id, group_id, limit=20):
    """دریافت پیام های کاربر در یک گروه خاص"""
    messages = []
    today = datetime.now().date()

    try:
        async for message in user_client.iter_messages(
            group_id, 
            from_user=target_user_id,
            limit=limit
        ):
            if message.date.date() == today:
                messages.append(message)
            else:
                break
    except Exception as e:
        print(f"خطا در دریافت پیام ها در گروه {group_id}: {e}")

    return messages

async def count_user_messages_in_group(user_client, target_user_id, group_id, limit=300):
    """شمارش پیام های کاربر در یک گروه خاص"""
    count = 0
    today = datetime.now().date()

    try:
        async for message in user_client.iter_messages(
            group_id, 
            from_user=target_user_id,
            limit=limit
        ):
            if message.date.date() == today:
                count += 1
            else:
                break
    except Exception as e:
        print(f"خطا در شمارش پیام ها در گروه {group_id}: {e}")

    return count

async def setup_commands(bot_client, user_client):
    """تنظیم دستورات ربات"""

    # دیکشنری برای ذخیره داده‌های گزارش
    report_data_store = {}

    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_command(event):
        welcome_msg = """
ربات مانیتور تلگرام - فعال

دستورات اصلی:
/add @username - افزودن کاربر به لیست مانیتور
/addid 123456 - افزودن کاربر با ID
/targets - مشاهده و مدیریت کاربران هدف  
/setforward ID - تنظیم مقصد فوروارد
/auto - شروع مانیتورینگ خودکار
/status - وضعیت ربات

دستورات پیشرفته:
/remove ID - حذف کاربر از لیست
/report - گزارش فعالیت امروز (با دکمه)
/help - راهنمای کامل

نکته: برای گرفتن ID از @userinfobot استفاده کنید
        """
        await event.reply(welcome_msg)

    @bot_client.on(events.NewMessage(pattern='/help'))
    async def help_command(event):
        help_msg = """
راهنمای کامل ربات:

مدیریت کاربران:
/add @username - افزودن کاربر با یوزرنیم
/addid 123456 - افزودن کاربر با ID
/targets - مشاهده لیست کاربران
/remove 123456 - حذف کاربر با ID

تنظیم مقصد:
/setforward -100123456 - تنظیم چت مقصد

گزارش گیری:
/report - گزارش پیام های امروز (با دکمه)
/status - وضعیت فعلی ربات

راه اندازی:
/auto - شروع مانیتورینگ
/start - نمایش منوی اصلی

پشتیبانی: در صورت مشکل پیام دهید
        """
        await event.reply(help_msg)

    @bot_client.on(events.NewMessage(pattern='/add (@?[\\w]+)'))
    async def add_target(event):
        username = event.pattern_match.group(1)
        try:
            user = await user_client.get_entity(username)
            if config_manager.add_target(user.id, username):
                await event.reply(f"کاربر {username} به لیست هدف اضافه شد\n\nID: {user.id}")
            else:
                await event.reply(f"کاربر {username} قبلا اضافه شده است")
        except Exception as e:
            await event.reply(f"خطا در پیدا کردن کاربر: {e}")

    @bot_client.on(events.NewMessage(pattern='/addid (\\d+)'))
    async def add_target_by_id(event):
        user_id = int(event.pattern_match.group(1))
        try:
            user = await user_client.get_entity(user_id)
            username = getattr(user, 'username', '')
            if config_manager.add_target(user_id, username):
                await event.reply(f"کاربر با ID {user_id} به لیست هدف اضافه شد")
            else:
                await event.reply(f"کاربر با ID {user_id} قبلا اضافه شده است")
        except Exception as e:
            await event.reply(f"خطا در پیدا کردن کاربر: {e}")

    @bot_client.on(events.NewMessage(pattern='/targets'))
    async def show_targets(event):
        targets = config_manager.get_targets_list()
        forward_to = config_manager.get_forward_chat()

        if not targets:
            await event.reply("لیست هدف خالی است\n\nاز دستور /add @username استفاده کنید")
            return

        msg = "کاربران تحت مانیتور:\n\n"
        for i, target in enumerate(targets, 1):
            username_display = f"@{target['username']}" if target['username'] else "بدون یوزرنیم"
            msg += f"{i}. {username_display}\n   ID: {target['user_id']}\n"

        if forward_to:
            msg += f"\nمقصد فوروارد: {forward_to}"
            msg += "\n\nوضعیت: آماده مانیتورینگ\nاز /auto برای شروع استفاده کنید"
        else:
            msg += "\nمقصد فوروارد تنظیم نشده\nاز /setforward استفاده کنید"

        await event.reply(msg)

    @bot_client.on(events.NewMessage(pattern='/setforward (-?\\d+)'))
    async def set_forward(event):
        chat_id = int(event.pattern_match.group(1))
        config_manager.set_forward(chat_id)
        await event.reply(f"مقصد فوروارد تنظیم شد\n\nچت ID: {chat_id}")

    @bot_client.on(events.NewMessage(pattern='/remove (\\d+)'))
    async def remove_target(event):
        user_id = int(event.pattern_match.group(1))
        if config_manager.remove_target(user_id):
            await event.reply(f"کاربر با ID {user_id} از لیست حذف شد")
        else:
            await event.reply(f"کاربر با ID {user_id} در لیست پیدا نشد")

    @bot_client.on(events.NewMessage(pattern='/status'))
    async def status_command(event):
        targets = config_manager.get_targets_list()
        forward_to = config_manager.get_forward_chat()

        status_msg = f"""
وضعیت ربات:

کاربران هدف: {len(targets)} نفر
مقصد فوروارد: {'تنظیم شده' if forward_to else 'تنظیم نشده'}
وضعیت: فعال و آماده

دستورات سریع:
/targets - مشاهده کاربران
/auto - شروع مانیتورینگ
        """
        await event.reply(status_msg)

    @bot_client.on(events.NewMessage(pattern='/auto'))
    async def auto_start(event):
        targets = config_manager.get_targets_list()
        forward_to = config_manager.get_forward_chat()

        if not targets:
            await event.reply("هیچ کاربری در لیست هدف نیست\n\nاز /add @username استفاده کنید")
            return

        if not forward_to:
            await event.reply("مقصد فوروارد تنظیم نشده\n\nاز /setforward ID استفاده کنید")
            return

        targets_list = "\n".join([f"• {t['username'] or t['user_id']}" for t in targets])

        await event.reply(f"""
مانیتورینگ خودکار فعال شد!

کاربران تحت نظر ({len(targets)} نفر):
{targets_list}

پیام ها به این چت فوروارد می شوند: {forward_to}

ربات به طور دائم فعال خواهد ماند
        """)

    @bot_client.on(events.NewMessage(pattern='/report'))
    async def daily_report(event):
        """گزارش فعالیت روزانه با دکمه"""
        targets = config_manager.get_targets_list()
        if not targets:
            await event.reply("هیچ کاربری در لیست هدف نیست")
            return

        processing_msg = await event.reply("در حال تهیه گزارش روزانه... لطفا صبر کنید")

        try:
            all_groups = await get_all_groups(user_client)

            if not all_groups:
                await processing_msg.edit("هیچ گروهی در حساب شما پیدا نشد")
                return

            report_id = f"report_{event.chat_id}_{int(datetime.now().timestamp())}"
            report_data = {
                'timestamp': datetime.now(),
                'targets': {}
            }

            report_lines = []
            report_lines.append("گزارش فعالیت امروز")
            report_lines.append(f"زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"تعداد گروه های شما: {len(all_groups)}")
            report_lines.append("")

            buttons = []

            for target_index, target in enumerate(targets):
                username = f"@{target['username']}" if target['username'] else f"ID: {target['user_id']}"
                report_lines.append(f"کاربر: {username}")

                common_groups_with_messages = 0  # فقط گروه‌هایی که پیام دارند
                total_messages = 0
                target_group_data = []

                for group in all_groups:
                    is_member = await check_user_in_group(user_client, group['id'], target['user_id'])

                    if is_member:
                        message_count = await count_user_messages_in_group(
                            user_client, target['user_id'], group['id']
                        )

                        if message_count > 0:  # فقط اگر پیامی داشته باشد
                            common_groups_with_messages += 1
                            total_messages += message_count

                            target_group_data.append({
                                'group_id': group['id'],
                                'group_title': group['title'],
                                'message_count': message_count
                            })

                report_data['targets'][target['user_id']] = {
                    'username': username,
                    'groups': target_group_data
                }

                report_lines.append(f"  گروه های مشترک با پیام: {common_groups_with_messages}")
                report_lines.append(f"  مجموع پیام ها: {total_messages}")

                # ایجاد دکمه برای هر گروه
                for group_data in target_group_data:
                    button_text = f"{group_data['group_title']} ({group_data['message_count']} پیام)"
                    callback_data = f"show_msgs:{target['user_id']}:{group_data['group_id']}:{report_id}"
                    buttons.append([KeyboardButtonCallback(button_text, callback_data.encode())])

                report_lines.append("")

            # ذخیره داده‌های گزارش
            report_data_store[report_id] = report_data

            report_text = "\n".join(report_lines)
            report_text += "\n\nبرای مشاهده پیام های هر گروه، روی دکمه زیر کلیک کنید:"

            # ارسال گزارش با دکمه‌ها
            await processing_msg.delete()
            if buttons:
                await event.reply(report_text, buttons=buttons)
            else:
                await event.reply(report_text + "\n\nهیچ گروهی با پیام پیدا نشد.")

        except Exception as e:
            await processing_msg.edit(f"خطا در تولید گزارش: {str(e)}")

    @bot_client.on(events.CallbackQuery)
    async def handle_callback(event):
        """مدیریت کلیک روی دکمه‌ها"""
        try:
            data = event.data.decode('utf-8')

            if data.startswith('show_msgs:'):
                parts = data.split(':')
                if len(parts) == 4:
                    target_user_id = int(parts[1])
                    group_id = int(parts[2])
                    report_id = parts[3]

                    await event.answer("در حال دریافت پیام ها...")

                    # پیدا کردن عنوان گروه
                    group_title = "گروه ناشناخته"
                    if report_id in report_data_store:
                        report_data = report_data_store[report_id]
                        for user_id, user_data in report_data['targets'].items():
                            if user_id == target_user_id:
                                for group in user_data['groups']:
                                    if group['group_id'] == group_id:
                                        group_title = group['group_title']
                                        break
                                break

                    # دریافت پیام‌ها
                    messages = await get_user_messages_in_group(user_client, target_user_id, group_id)

                    if not messages:
                        await event.edit("هیچ پیامی از این کاربر در این گروه پیدا نشد")
                        return

                    # ایجاد گزارش پیام‌ها
                    messages_text = f"پیام های کاربر در {group_title}:\n\n"

                    for i, message in enumerate(messages, 1):
                        message_time = message.date.strftime('%H:%M')
                        message_content = ""

                        if message.text:
                            if len(message.text) > 100:
                                message_content = message.text[:100] + "..."
                            else:
                                message_content = message.text
                        elif message.media:
                            message_content = "[مدیا]"
                        elif message.sticker:
                            message_content = "[استیکر]"
                        else:
                            message_content = "[پیام]"

                        # ایجاد لینک مستقیم به پیام
                        try:
                            chat_id_str = str(abs(group_id)).replace('100', '')
                            message_link = f"https://t.me/c/{chat_id_str}/{message.id}"
                            messages_text += f"{i}. زمان: {message_time}\n"
                            messages_text += f"   متن: {message_content}\n"
                            messages_text += f"   لینک: {message_link}\n\n"
                        except Exception:
                            messages_text += f"{i}. زمان: {message_time}\n"
                            messages_text += f"   متن: {message_content}\n\n"

                    # دکمه بازگشت
                    back_button = [[KeyboardButtonCallback("بازگشت به گزارش", f"back_to_report:{report_id}".encode())]]

                    if len(messages_text) > 4000:
                        # اگر متن طولانی شد، تقسیم می‌کنیم
                        parts = [messages_text[i:i+4000] for i in range(0, len(messages_text), 4000)]
                        for part in parts[:-1]:
                            await event.reply(part, link_preview=False)
                        await event.reply(parts[-1], buttons=back_button, link_preview=False)
                    else:
                        await event.edit(messages_text, buttons=back_button, link_preview=False)

            elif data.startswith('back_to_report:'):
                report_id = data.split(':')[1]

                if report_id in report_data_store:
                    report_data = report_data_store[report_id]

                    # بازسازی دکمه‌ها
                    buttons = []
                    for user_id, user_data in report_data['targets'].items():
                        for group in user_data['groups']:
                            button_text = f"{group['group_title']} ({group['message_count']} پیام)"
                            callback_data = f"show_msgs:{user_id}:{group['group_id']}:{report_id}"
                            buttons.append([KeyboardButtonCallback(button_text, callback_data.encode())])

                    report_text = f"گزارش فعالیت امروز\nزمان: {report_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\nبرای مشاهده پیام ها روی دکمه ها کلیک کنید:"

                    if buttons:
                        await event.edit(report_text, buttons=buttons)
                    else:
                        await event.edit(report_text + "\n\nهیچ گروهی با پیام پیدا نشد.")
                else:
                    await event.answer("گزارش منقضی شده است")

        except Exception as e:
            await event.answer(f"خطا: {str(e)}")

    # هندلر مانیتورینگ پیام ها
    @user_client.on(events.NewMessage())
    async def monitor_messages(event):
        targets = config_manager.get_targets_list()
        forward_to = config_manager.get_forward_chat()

        if not targets or not forward_to:
            return

        sender_id = event.sender_id
        is_target = any(target['user_id'] == sender_id for target in targets)

        if is_target:
            try:
                await event.message.forward_to(forward_to)
                logger.info(f"پیام از {sender_id} فوروارد شد")
            except Exception as e:
                logger.error(f"خطا در فوروارد: {e}")

async def main():
    print("\n" + "=" * 50)
    print("در حال راه اندازی ربات مانیتور تلگرام...")
    print("=" * 50 + "\n")

    config = config_manager.load_config()

    if config is None:
        print("اولین بار است که ربات را اجرا می کنید\n")
        config = await get_user_input()
        config_manager.save_config(config)
    else:
        print("تنظیمات قبلی پیدا شد")
        print(f"شماره: {config['phone']}")
        print("استفاده از تنظیمات قبلی...")

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

    try:
        await bot_client.start(bot_token=config['bot_token'])
        print("ربات متصل شد")

        await user_client.start(phone=config['phone'])
        print("اکانت کاربری متصل شد")
    except Exception as e:
        print(f"خطا در اتصال: {e}")
        return

    # ذخیره session برای دفعات بعد
    if hasattr(user_client.session, 'save'):
        try:
            session_string = user_client.session.save()
            if session_string != config.get('session', ''):
                config['session'] = session_string
                config_manager.save_config(config)
                print("Session ذخیره شد")
        except Exception as e:
            print(f"خطا در ذخیره session: {e}")

    print("\n" + "=" * 50)
    print("هر دو اکانت با موفقیت متصل شدند!")
    print("=" * 50 + "\n")

    await setup_commands(bot_client, user_client)

    print("ربات 24/7 فعال شد!")
    print("دستور /start را در ربات تلگرام ارسال کنید\n")

    targets = config_manager.get_targets_list()
    forward_to = config_manager.get_forward_chat()

    print("وضعیت فعلی:")
    print(f"کاربران هدف: {len(targets)} نفر")
    print(f"مقصد فوروارد: {'تنظیم شده' if forward_to else 'تنظیم نشده'}")
    print()

    try:
        # اجرای همزمان دو کلاینت با روش ساده‌تر
        print("ربات در حال اجرا است... برای توقف از Ctrl+C استفاده کنید")

        # ایجاد تسک‌ها
        bot_task = asyncio.ensure_future(bot_client.run_until_disconnected())
        user_task = asyncio.ensure_future(user_client.run_until_disconnected())

        # منتظر ماندن تا یکی از تسک‌ها کامل شود
        await asyncio.wait([bot_task, user_task], return_when=asyncio.FIRST_COMPLETED)

    except KeyboardInterrupt:
        print("\nربات به صورت کنترل شده متوقف شد")
    except Exception as e:
        print(f"خطا در اجرای ربات: {e}")
    finally:
        # اتصال را قطع کن
        await bot_client.disconnect()
        await user_client.disconnect()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nربات متوقف شد")
    except Exception as e:
        print(f"خطا رخ داد: {e}")
