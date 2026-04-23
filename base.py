import sqlite3
from datetime import datetime


class SQL:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    def add_user(self, user_id):
        query = "INSERT INTO users (id) VALUES (?)"
        with self.connection:
            self.cursor.execute(query, (user_id,))

    def user_exist(self, user_id):
        query = "SELECT id FROM users WHERE id = ?"
        with self.connection:
            result = self.cursor.execute(query, (user_id,)).fetchone()
            return result is not None

    def get_field(self, user_id, field):
        query = f"SELECT {field} FROM users WHERE id = ?"
        with self.connection:
            result = self.cursor.execute(query, (user_id,)).fetchone()
            return result[0] if result else None

    def update_field(self, user_id, field, value):
        query = f"UPDATE users SET {field} = ? WHERE id = ?"
        with self.connection:
            self.cursor.execute(query, (value, user_id))

    def add_event(self, user_id, name, comment, event_time):
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        query = "INSERT INTO events (id, name, comment, time, current_time) VALUES (?, ?, ?, ?, ?)"
        with self.connection:
            self.cursor.execute(query, (user_id, name, comment, event_time, current_time))
            return self.cursor.lastrowid

    def get_user_events(self, user_id):
        query = "SELECT event_id, name, time, current_time FROM events WHERE id = ? ORDER BY time"
        with self.connection:
            return self.cursor.execute(query, (user_id,)).fetchall()

    def get_event_by_id(self, event_id):
        query = "SELECT event_id, name, comment, time, current_time FROM events WHERE event_id = ?"
        with self.connection:
            return self.cursor.execute(query, (event_id,)).fetchone()

    def delete_event(self, event_id):
        with self.connection:
            self.cursor.execute("DELETE FROM reminders WHERE event_id = ?", (event_id,))
            self.cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))

    def add_reminder(self, event_id, remind_at, type_remind):
        query = "INSERT INTO reminders (event_id, remind_at, type_remind, is_sent) VALUES (?, ?, ?, 0)"
        with self.connection:
            self.cursor.execute(query, (event_id, remind_at, type_remind))
            return self.cursor.lastrowid

    def get_pending_reminders(self, now_str):
        # Возвращаем все неотправленные — проверка времени идёт в scheduler через now >= remind_dt
        query = """
            SELECT r.id, r.event_id, r.remind_at, r.type_remind,
                   e.name, e.comment, e.time, e.id
            FROM reminders r
            JOIN events e ON r.event_id = e.event_id
            WHERE r.is_sent = 0
        """
        with self.connection:
            return self.cursor.execute(query, ()).fetchall()

    def mark_sent(self, reminder_id):
        query = "UPDATE reminders SET is_sent = 1 WHERE id = ?"
        with self.connection:
            self.cursor.execute(query, (reminder_id,))

    def close(self):
        self.connection.close()
