import asyncio
from datetime import datetime
from aiogram import Bot


async def reminder_scheduler(bot: Bot, db):
    while True:
        try:
            # Получаем текущее время в нужном формате
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:00")
            # Ищем напоминания для отправки
            reminders = db.get_reminders_to_send(now_str)
            if reminders:
                print(f"Найдено {len(reminders)} напоминаний для отправки")

                for reminder in reminders:
                    reminder_id, user_id, event_id, name, comment, event_time, remind_at = reminder

                    try:
                        # Преобразуем время события в datetime
                        if isinstance(event_time, str):
                            event_time_obj = datetime.strptime(event_time, "%Y-%m-%d %H:%M:%S")
                        else:
                            event_time_obj = event_time

                        # Вычисляем сколько осталось времени
                        time_left = event_time_obj - now
                        days_left = time_left.days
                        hours_left = time_left.seconds // 3600
                        minutes_left = (time_left.seconds % 3600) // 60

                        # Формируем сообщение
                        if days_left > 0:
                            time_text = f"Осталось {days_left} дн {hours_left} ч"
                        elif hours_left > 0:
                            time_text = f"Осталось {hours_left} ч {minutes_left} мин"
                        else:
                            time_text = f"Осталось {minutes_left} мин"

                        message_text = (
                            f"🔔 НАПОМИНАНИЕ 🔔\n\n"
                            f"📌 {name}\n"
                            f"📝 {comment if comment != '-' else 'Без описания'}\n"
                            f"🕒 {event_time.strftime('%d.%m.%Y в %H:%M')}\n"
                            f"⏳ {time_text}"
                        )

                        # Отправляем сообщение
                        await bot.send_message(chat_id=user_id, text=message_text)

                        # Отмечаем как отправленное
                        db.mark_reminder_as_sent(reminder_id)
                        print(f"✅ Отправлено напоминание {reminder_id} пользователю {user_id}")

                    except Exception as e:
                        print(f"❌ Ошибка отправки напоминания {reminder_id}: {e}")

            # Ждем 60 секунд
            await asyncio.sleep(60)

        except Exception as e:
            print(f"❌ Ошибка в планировщике: {e}")
            await asyncio.sleep(30)