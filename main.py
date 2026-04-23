import config
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.client.session.aiohttp import AiohttpSession
from datetime import datetime
from base import SQL
from schedule import reminder_scheduler

# --- Инициализация ---
session = AiohttpSession(proxy='http://proxy.server:3128')
bot = Bot(token=config.TOKEN, session=session)
db = SQL('db.db')
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- Клавиатуры ---
kb_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Добавить событие", callback_data="new_event")],
    [InlineKeyboardButton(text="📋 Мои события", callback_data="my_events")]
])

kb_frequency = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Один раз", callback_data="freq_once")],
    [InlineKeyboardButton(text="Каждый день", callback_data="freq_daily")],
    [InlineKeyboardButton(text="Каждую неделю", callback_data="freq_weekly")],
    [InlineKeyboardButton(text="Каждый месяц", callback_data="freq_monthly")],
    [InlineKeyboardButton(text="⚙️ По умолчанию (за день и час)", callback_data="freq_default")]
])

kb_confirm = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes")],
    [InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no")]
])

# За сколько напомнить — для каждого типа повтора своя клавиатура
kb_advance_once = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⏰ За 5 минут", callback_data="adv_5m")],
    [InlineKeyboardButton(text="⏰ За 10 минут", callback_data="adv_10m")],
    [InlineKeyboardButton(text="⏰ За 30 минут", callback_data="adv_30m")],
    [InlineKeyboardButton(text="🔔 В момент события", callback_data="adv_0m")]
])

kb_advance_daily = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⏰ За 1 час", callback_data="adv_60m")],
    [InlineKeyboardButton(text="⏰ За 3 часа", callback_data="adv_180m")],
    [InlineKeyboardButton(text="⏰ За 6 часов", callback_data="adv_360m")],
    [InlineKeyboardButton(text="🔔 В момент события", callback_data="adv_0m")]
])

kb_advance_weekly = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📅 За 1 день", callback_data="adv_1440m")],
    [InlineKeyboardButton(text="📅 За 3 дня", callback_data="adv_4320m")],
    [InlineKeyboardButton(text="🔔 В момент события", callback_data="adv_0m")]
])

kb_advance_monthly = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📅 За 1 день", callback_data="adv_1440m")],
    [InlineKeyboardButton(text="📅 За 3 дня", callback_data="adv_4320m")],
    [InlineKeyboardButton(text="📅 За 1 неделю", callback_data="adv_10080m")],
    [InlineKeyboardButton(text="🔔 В момент события", callback_data="adv_0m")]
])

# Карта: тип повтора -> клавиатура выбора времени
FREQ_ADVANCE_KB = {
    "once": kb_advance_once,
    "daily": kb_advance_daily,
    "weekly": kb_advance_weekly,
    "monthly": kb_advance_monthly,
}

# Метки для advance кнопок
ADVANCE_LABELS = {
    "adv_0m":     (0,     "В момент события"),
    "adv_5m":     (5,     "За 5 минут"),
    "adv_10m":    (10,    "За 10 минут"),
    "adv_30m":    (30,    "За 30 минут"),
    "adv_60m":    (60,    "За 1 час"),
    "adv_180m":   (180,   "За 3 часа"),
    "adv_360m":   (360,   "За 6 часов"),
    "adv_1440m":  (1440,  "За 1 день"),
    "adv_4320m":  (4320,  "За 3 дня"),
    "adv_10080m": (10080, "За 1 неделю"),
}

kb_start = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/start")]],
    resize_keyboard=True
)

FREQ_LABELS = {
    "freq_once": ("once", "Один раз"),
    "freq_daily": ("daily", "Каждый день"),
    "freq_weekly": ("weekly", "Каждую неделю"),
    "freq_monthly": ("monthly", "Каждый месяц")
}


def ensure_user(user_id):
    if not db.user_exist(user_id):
        db.add_user(user_id)


# --- Сообщения ---
@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    ensure_user(user_id)

    if message.text == "/start":
        db.update_field(user_id, "status", 1)
        await message.answer("Главное меню:", reply_markup=kb_menu)
        await message.answer("Используй кнопку ниже для быстрого старта:", reply_markup=kb_start)
        return

    status = db.get_field(user_id, "status")

    # Статус 2: ждём название
    if status == 2:
        db.update_field(user_id, "name", message.text)
        db.update_field(user_id, "status", 3)
        await message.answer('Введите комментарий к событию (или "-" если не нужен):')

    # Статус 3: ждём комментарий
    elif status == 3:
        db.update_field(user_id, "comment", message.text)
        db.update_field(user_id, "status", 4)
        await message.answer("Укажи дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ\nПример: 28.05.2026 15:30")

    # Статус 4: ждём дату и время
    elif status == 4:
        try:
            event_dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
            if event_dt <= datetime.now():
                await message.answer(
                    f"Нельзя создать событие в прошлом!\n"
                    f"Ты ввёл: {event_dt.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Сейчас: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                    f"Введи будущую дату:"
                )
                return
            db.update_field(user_id, "event_time", event_dt.strftime("%d.%m.%Y %H:%M"))
            db.update_field(user_id, "status", 5)
            await message.answer("Как часто напоминать?", reply_markup=kb_frequency)
        except ValueError:
            await message.answer("Неправильный формат! Пример: 28.05.2026 15:30")


# --- Inline-кнопки ---
@dp.callback_query()
async def handle_callback(call: CallbackQuery):
    user_id = call.from_user.id
    ensure_user(user_id)
    await call.answer()

    if call.data == "new_event":
        db.update_field(user_id, "name", "")
        db.update_field(user_id, "comment", "")
        db.update_field(user_id, "event_time", "")
        db.update_field(user_id, "type_remind", "")
        db.update_field(user_id, "status", 2)
        await call.message.answer("Введите название события:")

    elif call.data == "my_events":
        events = db.get_user_events(user_id)
        if not events:
            await call.message.answer("У тебя пока нет событий.")
        else:
            text = "📋 Твои события:\n\n"
            for ev_id, name, ev_time in events:
                try:
                    dt = datetime.strptime(ev_time, "%d.%m.%Y %H:%M")
                    text += f"📌 {name} — {dt.strftime('%d.%m.%Y %H:%M')}\n"
                except Exception:
                    text += f"📌 {name} — {ev_time}\n"
            await call.message.answer(text)

    elif call.data in FREQ_LABELS:
        freq_type, freq_label = FREQ_LABELS[call.data]
        db.update_field(user_id, "type_remind", freq_type)
        db.update_field(user_id, "status", 7)
        await call.message.answer(
            f"Выбрано: {freq_label}\nЗа сколько времени напомнить?",
            reply_markup=FREQ_ADVANCE_KB[freq_type]
        )

    elif call.data == "freq_default":
        from datetime import timedelta
        name = db.get_field(user_id, "name")
        comment = db.get_field(user_id, "comment")
        event_time_str = db.get_field(user_id, "event_time")
        event_dt = datetime.strptime(event_time_str, "%d.%m.%Y %H:%M")

        db.update_field(user_id, "type_remind", "default")
        db.update_field(user_id, "status", 6)

        await call.message.answer(
            f"📝 Подтверди событие:\n\n"
            f"📌 Название: {name}\n"
            f"💬 Комментарий: {comment if comment != '-' else 'Нет'}\n"
            f"🕒 Время: {event_dt.strftime('%d.%m.%Y в %H:%M')}\n"
            f"🔔 Напоминание: за 1 день и за 1 час до события\n\n"
            f"Всё верно?",
            reply_markup=kb_confirm
        )

    elif call.data in ADVANCE_LABELS:
        minutes, advance_label = ADVANCE_LABELS[call.data]
        freq_type = db.get_field(user_id, "type_remind")
        db.update_field(user_id, "type_remind", f"{freq_type}_{minutes}")
        db.update_field(user_id, "status", 6)

        name = db.get_field(user_id, "name")
        comment = db.get_field(user_id, "comment")
        event_time_str = db.get_field(user_id, "event_time")
        event_dt = datetime.strptime(event_time_str, "%d.%m.%Y %H:%M")

        freq_label = dict(v for v in FREQ_LABELS.values()).get(freq_type, freq_type)
        repeat_text = "Один раз" if freq_type == "once" else f"🔁 {freq_label}"

        await call.message.answer(
            f"📝 Подтверди событие:\n\n"
            f"📌 Название: {name}\n"
            f"💬 Комментарий: {comment if comment != '-' else 'Нет'}\n"
            f"🕒 Время: {event_dt.strftime('%d.%m.%Y в %H:%M')}\n"
            f"🔁 Повтор: {repeat_text}\n"
            f"🔔 Напоминание: {advance_label}\n\n"
            f"Всё верно?",
            reply_markup=kb_confirm
        )

    elif call.data == "confirm_yes":
        from datetime import timedelta
        name = db.get_field(user_id, "name")
        comment = db.get_field(user_id, "comment")
        event_time_str = db.get_field(user_id, "event_time")
        type_remind = db.get_field(user_id, "type_remind")

        event_dt = datetime.strptime(event_time_str, "%d.%m.%Y %H:%M")
        event_id = db.add_event(user_id, name, comment, event_time_str)

        if type_remind == "default":
            remind_day = (event_dt - timedelta(minutes=1440)).strftime("%d.%m.%Y %H:%M")
            remind_hour = (event_dt - timedelta(minutes=60)).strftime("%d.%m.%Y %H:%M")
            db.add_reminder(event_id, remind_day, "once")
            db.add_reminder(event_id, remind_hour, "once")
        else:
            parts = type_remind.split("_") if type_remind else ["once", "0"]
            reminder_type = parts[0]
            minutes_before = int(parts[1]) if len(parts) > 1 else 0
            remind_at_str = (event_dt - timedelta(minutes=minutes_before)).strftime("%d.%m.%Y %H:%M")
            db.add_reminder(event_id, remind_at_str, reminder_type)

        db.update_field(user_id, "status", 1)
        await call.message.answer(f"✅ Событие «{name}» сохранено! Напомню в нужное время.")

    elif call.data == "confirm_no":
        db.update_field(user_id, "status", 1)
        await call.message.answer("Отменено. Возвращаю в меню.", reply_markup=kb_menu)


# --- Запуск ---
async def main():
    asyncio.create_task(reminder_scheduler(bot, db))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
