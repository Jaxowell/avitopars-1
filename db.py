import sqlite3
import logging

class Database:
    
    def __init__(self, logger: logging.Logger):
        
        self.logger = logger
        self.conn = sqlite3.connect('ads.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS ads (user_id INTEGER NOT NULL, ad_id TEXT, PRIMARY KEY (user_id, ad_id))")
        # Проверка на существование колонки user_id в таблице ads
        self.cursor.execute("PRAGMA table_info(ads)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if 'user_id' not in columns:
            # Добавление колонки user_id, если она отсутствует
            self.cursor.execute("ALTER TABLE ads ADD COLUMN user_id INTEGER")
            self.conn.commit()
            self.logger.info("Добавлена колонка user_id в таблицу ads.")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_urls (user_id INTEGER PRIMARY KEY, url TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_state (user_id INTEGER PRIMARY KEY, url TEXT, is_running BOOLEAN)")
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS authorized_users (user_id INTEGER PRIMARY KEY)""")
        self.conn.commit()

        self.conn.commit()

    # ---- Методы для авторизации пользователей ----

    def is_authorized(self, user_id):
        self.cursor.execute("SELECT 1 FROM authorized_users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone() is not None

    def authorize_user(self, user_id):
        """Авторизует нового пользователя."""
        self.cursor.execute("INSERT OR REPLACE INTO authorized_users (user_id) VALUES (?)", (user_id,))
        self.conn.commit()
        self.logger.info(f"Пользователь {user_id} успешно авторизован.")

    def save_url(self, user_id, url):
        self.cursor.execute("INSERT OR REPLACE INTO user_urls (user_id, url) VALUES (?, ?)", (user_id, url, ))
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
    
    def save_user_state_running(self, user_id, is_running):
        self.cursor.execute("UPDATE user_state SET is_running = ? WHERE user_id = ?", (is_running, user_id))
        self.conn.commit()

    def save_user_state_url(self, user_id, url):
        self.cursor.execute("UPDATE user_state SET url = ? WHERE user_id = ?", (url, user_id))
        self.conn.commit()

    def load_user_state(self, user_id=None):
        if user_id:
            self.cursor.execute("SELECT user_id, url, is_running FROM user_state WHERE user_id = ?", (user_id,))
        else:
            self.cursor.execute("SELECT user_id, url, is_running FROM user_state")
        rows = self.cursor.fetchall()
        return {row[0]: {'url': row[1], 'is_running': row[2]} for row in rows}


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

        ads_to_keep = (current_ads + new_ad_ids)[-20:]  # Оставляем только последние 20
        self.cursor.execute("DELETE FROM ads WHERE user_id = ?", (user_id,))
        self.conn.commit()

        self.cursor.executemany(
            "INSERT INTO ads (user_id, ad_id) VALUES (?, ?)", 
            [(user_id, ad_id) for ad_id in ads_to_keep]
        )
        self.conn.commit()
        self.logger.info(f"Обновлены последние 20 ID объявлений для пользователя {user_id}: {ads_to_keep}")



    
    