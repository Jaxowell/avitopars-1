import sqlite3
import logging

class Database:
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.conn = sqlite3.connect('ads.db')
        self.cursor = self.conn.cursor()

        # Создание таблицы ads, если она отсутствует
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            user_id INTEGER NOT NULL,
            ad_id TEXT,
            PRIMARY KEY (user_id, ad_id)
        )
        """)

        # Добавляем новую колонку, если её ещё нет
        self.cursor.execute("PRAGMA table_info(user_state)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if 'in_url_menu' not in columns:
            self.cursor.execute("ALTER TABLE user_state ADD COLUMN in_url_menu BOOLEAN DEFAULT False")
            self.conn.commit()
        
        if 'previous_menu' not in columns:
            self.cursor.execute("ALTER TABLE user_state ADD COLUMN previous_menu TEXT DEFAULT NULL")
            self.conn.commit()
            self.logger.info("Добавлена колонка previous_menu в таблицу user_state.")

        # Проверка на существование колонки user_id в таблице ads
        self.cursor.execute("PRAGMA table_info(ads)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if 'user_id' not in columns:
            self.cursor.execute("ALTER TABLE ads ADD COLUMN user_id INTEGER")
            self.conn.commit()
            self.logger.info("Добавлена колонка user_id в таблицу ads.")

        # Создание таблицы user_urls, если она отсутствует
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            name TEXT NOT NULL,
            UNIQUE(user_id, url)
        )
        """)

        # Проверка на существование колонки name в таблице user_urls
        self.cursor.execute("PRAGMA table_info(user_urls)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if 'name' not in columns:
            self.cursor.execute("ALTER TABLE user_urls ADD COLUMN name TEXT")
            self.conn.commit()
            self.logger.info("Добавлена колонка name в таблицу user_urls.")

        # Создание остальных таблиц
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER PRIMARY KEY,
            url TEXT,
            is_running BOOLEAN
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            user_id INTEGER PRIMARY KEY
        )
        """)


    def is_authorized(self, user_id):
        self.cursor.execute("SELECT 1 FROM authorized_users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def authorize_user(self, user_id):
        """Авторизует нового пользователя."""
        self.cursor.execute("INSERT OR REPLACE INTO authorized_users (user_id) VALUES (?)", (user_id,))
        self.conn.commit()
        self.logger.info(f"Пользователь {user_id} успешно авторизован.")

    def save_url(self, user_id, url, name):
        self.cursor.execute(
            "INSERT INTO user_urls (user_id, url, name) VALUES (?, ?, ?)",
            (user_id, url, name)
        )
        self.conn.commit()

    def get_user_urls(self, user_id):
        self.cursor.execute("SELECT url, name FROM user_urls WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()

    def delete_url(self, user_id, url):
        self.cursor.execute("DELETE FROM user_urls WHERE user_id = ? AND url = ?", (user_id, url))
        self.conn.commit()

    def load_url(self, user_id):
        self.cursor.execute(f"SELECT url FROM user_urls WHERE user_id = {user_id}")
        result = self.cursor.fetchone()
        return result
    
    def del_urls_from_ads(self, user_id):
        self.cursor.execute(f"DELETE FROM ads WHERE user_id = {user_id}")
        self.conn.commit()
        
    def save_user_state(self, user_id, url, is_running):
        self.cursor.execute("INSERT OR REPLACE INTO user_state (user_id, url, is_running) VALUES (?, ?, ?)", (user_id, url, is_running,))
        self.conn.commit()

    def save_user_state_menu(self, user_id, in_url_menu=False):
        self.logger.info(f"Сохранение состояния пользователя {user_id}: in_url_menu={in_url_menu}")
        self.cursor.execute("""
            INSERT INTO user_state (user_id, in_url_menu)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET in_url_menu = ?
        """, (user_id, in_url_menu, in_url_menu))
        self.conn.commit()

    def save_user_state_running(self, user_id, is_running):
        self.cursor.execute("UPDATE user_state SET is_running = ? WHERE user_id = ?", (is_running, user_id))
        self.conn.commit()

    def save_user_state_url(self, user_id, url):
        self.cursor.execute("UPDATE user_state SET url = ? WHERE user_id = ?", (url, user_id))
        self.conn.commit()

    def load_user_state(self, user_id):
        """Загружает состояние пользователя."""
        self.cursor.execute("""
            SELECT user_id, url, is_running, in_url_menu FROM user_state WHERE user_id = ?
        """, (user_id,))
        row = self.cursor.fetchone()
        if row:
            return {row[0]: {'url': row[1], 'is_running': row[2], 'in_url_menu': row[3]}}
        return {}

    def add_ad_id(self, user_id, ad_id):
        try:
            self.logger.info(f"Добавление ID объявления {ad_id} для пользователя {user_id}")
            self.cursor.execute("INSERT INTO ads (user_id, ad_id) VALUES (?, ?)", (user_id, ad_id))
            self.conn.commit()
            self.logger.info(f"Успешно добавлен ID объявления {ad_id} для пользователя {user_id}")
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"ID объявления {ad_id} для пользователя {user_id} уже существует: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка при добавлении ID {ad_id} для пользователя {user_id}: {e}")

    def is_ad_seen(self, user_id, ad_id):
        self.cursor.execute("SELECT 1 FROM ads WHERE user_id = ? AND ad_id = ?", (user_id, ad_id))
        return self.cursor.fetchone() is not None

    def replace_oldest_ads(self, user_id, new_ad_ids):
        self.cursor.execute("SELECT ad_id FROM ads WHERE user_id = ? ORDER BY rowid ASC", (user_id,))
        current_ads = [row[0] for row in self.cursor.fetchall()]

        ads_to_keep = (current_ads + new_ad_ids)[-20:]  # Оставляем последние 20
        self.cursor.execute("DELETE FROM ads WHERE user_id = ?", (user_id,))
        self.conn.commit()

        self.cursor.executemany(
            "INSERT INTO ads (user_id, ad_id) VALUES (?, ?)", 
            [(user_id, ad_id) for ad_id in ads_to_keep]
        )
        self.conn.commit()
        self.logger.info(f"Обновлены последние 20 ID объявлений для пользователя {user_id}.")
    
    def reset_user_menu_state(self, user_id):
        self.cursor.execute("UPDATE user_state SET in_url_menu = False WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def save_user_previous_menu(self, user_id, previous_menu):
        self.cursor.execute("UPDATE user_state SET previous_menu = ? WHERE user_id = ?", (previous_menu, user_id))
        self.conn.commit()

    def save_user_state_menu(self, user_id, in_url_menu=False):
        self.logger.info(f"Сохранение состояния пользователя {user_id}: in_url_menu={in_url_menu}")
        self.cursor.execute("""
            INSERT INTO user_state (user_id, in_url_menu)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET in_url_menu = ?
        """, (user_id, in_url_menu, in_url_menu))
        self.conn.commit()