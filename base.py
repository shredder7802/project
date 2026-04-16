import sqlite3

class SQL:
    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    # Добавление пользователя в БД
    def add_user(self, id):
        query = "INSERT INTO users (id) VALUES(?)"
        with self.connection:
            return self.cursor.execute(query, (id,))

    # Проверка, есть ли пользователь в БД
    def user_exist(self, id):
        query = "SELECT * FROM users WHERE id = ?"
        with self.connection:
            result = self.cursor.execute(query, (id,)).fetchall()
            return bool(len(result))

    # Получить значение поля
    def get_field(self, table, id, field):
        query = f"SELECT {field} FROM {table} WHERE id = ?"
        with self.connection:
            result = self.cursor.execute(query, (id,)).fetchone()
            if result:
                return result[0]

    # Обновить значение поля
    def update_field(self, table, id, field, value):
        query = f"UPDATE {table} SET {field} = ? WHERE id = ?"
        with self.connection:
            self.cursor.execute(query, (value, id))


    def add_event(self, name, comment, time, id):
        query = "INSERT INTO events (name, comment, time, id) VALUES(?,?,?,?)"
        with self.connection:
            return self.cursor.execute(query, (name, comment, time, id))

    def close(self):
        self.connection.close()

    # Добавь эти методы в класс SQL в файл base.py

    # Добавление события с возвратом ID
    def add_event_and_get_id(self, name, comment, time, user_id):
        query = "INSERT INTO events (name, comment, time, user_id) VALUES(?,?,?,?)"
        with self.connection:
            self.cursor.execute(query, (name, comment, time, user_id))
            return self.cursor.lastrowid

    # Сохранение напоминания
    def add_reminder(self, user_id, event_id, title, description, event_time, remind_at, reminder_type='once'):
        query = """INSERT INTO reminders 
                   (user_id, event_id, title, description, event_time, remind_at, reminder_type) 
                   VALUES(?,?,?,?,?,?,?)"""
        with self.connection:
            self.cursor.execute(query, (user_id, event_id, title, description, event_time, remind_at, reminder_type))
            return self.cursor.lastrowid

    # Получить все неотправленные напоминания до указанного времени
    def get_reminders_to_send(self, current_time):
        query = """SELECT id, user_id, event_id, title, description, event_time, remind_at 
                   FROM reminders 
                   WHERE remind_at <= ? AND is_sent = 0"""
        with self.connection:
            return self.cursor.execute(query, (current_time,)).fetchall()

    # Отметить напоминание как отправленное
    def mark_reminder_as_sent(self, reminder_id):
        query = "UPDATE reminders SET is_sent = 1 WHERE id = ?"
        with self.connection:
            self.cursor.execute(query, (reminder_id,))

    # Получить время события по event_id
    def get_event_time_by_id(self, event_id):
        query = "SELECT time FROM events WHERE id = ?"
        with self.connection:
            result = self.cursor.execute(query, (event_id,)).fetchone()
            if result:
                return result[0]
        return None

    # Обновить статус пользователя (уже есть, но добавлю для ясности)
    def update_status(self, user_id, status):
        query = "UPDATE users SET status = ? WHERE id = ?"
        with self.connection:
            self.cursor.execute(query, (status, user_id))
