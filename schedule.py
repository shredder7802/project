import asyncio
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from aiogram import Bot


async def reminder_scheduler(bot: Bot, db):
    """Фоновая задача: каждую минуту проверяет и отправляет напоминания."""
    while True:
        try:
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:00")
            reminders = db.get_pending_reminders(now_str)

            for row in reminders:
                reminder_id, event_id, remind_at, type_remind, name, comment, event_time_str, user_id = row
                try:
                    event_dt = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
                    text = (
                        f"🔔 Напоминание!\n\n"
                        f"📌 {name}\n"
                        f"� {commentt if comment and comment != '-' else 'Без описания'}\n"
                        f"🕒 Начало: {event_dt.strftime('%d.%m.%Y в %H:%M')}"
                    )
                    await bot.send_message(chat_id=user_id, text=text)
                    db.mark_sent(reminder_id)

                    # Создаём следующее напоминание для повторяющихся
                    if type_remind == "daily":
                        next_dt = event_dt + timedelta(days=1)
                    elif type_remind == "weekly":
                        next_dt = event_dt + timedelta(weeks=1)
                    elif type_remind == "monthly":
                        next_dt = event_dt + relativedelta(months=1)
                    else:
                        next_dt = None

                    if next_dt:
                        next_str = next_dt.strftime("%Y-%m-%d %H:%M:%S")
                        new_event_id = db.add_event(user_id, name, comment, next_str)
                        db.add_reminder(new_event_id, next_str, type_remind)

                except Exception as e:
                    print(f"Ошибка отправки напоминания {reminder_id}: {e}")

        except Exception as e:
            print(f"Ошибка планировщика: {e}")

        await asyncio.sleep(60)
