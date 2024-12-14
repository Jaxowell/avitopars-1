import sqlite3
from functools import wraps
import logging

log: logging.Logger
url = "ads.db"


def db_connection(url_to_db: str):
    def decorator(func):
        @wraps(func)
        def wrapped(**kwargs):
            connection = sqlite3.connect(url_to_db)
            cursor = connection.cursor()
            result = func(cursor, **kwargs)
            connection.commit()
            connection.close()
            return result

        return wrapped

    return decorator


def init_db(logger: logging.Logger):
    global log
    log = logger

    # Создание таблицы ads, если она отсутствует
    create_ads_table()

    # Создание таблицы user_urls, если она отсутствует
    create_userurls_table()

    # Создание таблицы состояния ссылок
    create_userstate_table()
    # Добавляем таблицу с авторизированными пользователями
    create_auth_table()
    # Добавляем таблицу для ослеживания тех, кто запустил парсинг
    create_userparsing_table()


@db_connection(url)
def create_ads_table(cursor: sqlite3.Cursor):
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS ads (
        user_id INTEGER NOT NULL,
        ad_id TEXT,
        PRIMARY KEY (user_id, ad_id)
    )
    """
    )


@db_connection(url)
def create_userurls_table(cursor: sqlite3.Cursor):
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        url TEXT NOT NULL,
        name TEXT NOT NULL,
        UNIQUE(user_id, url)
    )
    """
    )


@db_connection(url)
def create_userstate_table(cursor: sqlite3.Cursor):
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS user_state (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, url TEXT, is_running BOOLEAN)"
    )


@db_connection(url)
def create_userparsing_table(cursor: sqlite3.Cursor):
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_parsing (
        user_id INTEGER PRIMARY KEY,
        parsing BOOLEAN
    )
    """
    )


@db_connection(url)
def create_auth_table(cursor: sqlite3.Cursor):
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS authorized_users (
        user_id INTEGER PRIMARY KEY
    )
    """
    )


@db_connection(url)
def is_authorized(cursor: sqlite3.Cursor, user_id):
    cursor.execute("SELECT 1 FROM authorized_users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


@db_connection(url)
def authorize_user(cursor: sqlite3.Cursor, user_id):
    global log
    """Авторизует нового пользователя."""
    cursor.execute(
        "INSERT OR REPLACE INTO authorized_users (user_id) VALUES (?)", (user_id,)
    )
    log.info(f"Пользователь {user_id} успешно авторизован.")


@db_connection(url)
def save_url(cursor: sqlite3.Cursor, user_id, url, name):
    cursor.execute(
        "INSERT INTO user_urls (user_id, url, name) VALUES (?, ?, ?)",
        (user_id, url, name),
    )


@db_connection(url)
def set_parsing_status(cursor: sqlite3.Cursor, user_id, parsing):
    cursor.execute(
        "INSERT OR REPLACE INTO user_parsing (user_id, parsing) VALUES (?, ?)",
        (user_id, parsing),
    )


@db_connection(url)
def get_parsing_status(cursor: sqlite3.Cursor, user_id):
    cursor.execute(f"SELECT parsing FROM user_parsing WHERE user_id = {user_id}")
    res = cursor.fetchone()
    if res == None:
        return 3
    return res[0]


@db_connection(url)
def get_user_urls(cursor: sqlite3.Cursor, user_id):
    cursor.execute(f"SELECT url, name FROM user_urls WHERE user_id = {user_id}")
    return cursor.fetchall()


@db_connection(url)
def delete_url(cursor: sqlite3.Cursor, user_id, url_name):
    cursor.execute(
        "DELETE FROM user_urls WHERE user_id = ? AND name = ?", (user_id, url_name)
    )


@db_connection(url)
def get_url(cursor: sqlite3.Cursor, user_id, url_name):
    cursor.execute(
        f"SELECT url FROM user_urls WHERE user_id = '{user_id}' AND name = '{url_name}'"
    )
    result = cursor.fetchone()[0]
    return result


@db_connection(url)
def get_url_state(cursor: sqlite3.Cursor, url: str, user_id: int) -> bool:
    cursor.execute(
        "SELECT is_running FROM user_state WHERE user_id = ? AND url = ?",
        (user_id, url),
    )
    result = bool(cursor.fetchone()[0])
    return result


@db_connection(url)
def get_urls_states(cursor: sqlite3.Cursor, user_id: int) -> list[bool]:
    cursor.execute(
        f"SELECT is_running FROM user_state WHERE user_id = {user_id} AND url = '{url}'"
    )
    result = list(bool(row[2]) for row in cursor.fetchall())
    return result


@db_connection(url)
def del_urls_from_ads(cursor: sqlite3.Cursor, user_id):
    cursor.execute(f"DELETE FROM ads WHERE user_id = {user_id}")


@db_connection(url)
def save_url_state(cursor: sqlite3.Cursor, user_id, url, is_running):
    cursor.execute(
        "INSERT INTO user_state (user_id, url, is_running) VALUES (?, ?, ?)",
        (user_id, url, is_running),
    )


@db_connection(url)
def set_url_state(cursor: sqlite3.Cursor, user_id, url, is_running):
    cursor.execute(
        "UPDATE user_state SET is_running = ? WHERE url = ? AND user_id = ?",
        (is_running, url, user_id),
    )


@db_connection(url)
def load_user_state(cursor: sqlite3.Cursor, user_id, url_name):
    """Загружает состояние пользователя."""
    cursor.execute(
        """
        SELECT user_id, url, is_running FROM user_state WHERE user_id = ? AND name = ?
    """,
        (user_id, url_name),
    )
    row = cursor.fetchone()
    if row:
        return {row[0]: {"url": row[1], "is_running": row[2]}}
    return {}


@db_connection(url)
def add_ad_id(cursor: sqlite3.Cursor, user_id, ad_id):
    try:
        log.info(f"Добавление ID объявления {ad_id} для пользователя {user_id}")
        cursor.execute(
            "INSERT INTO ads (user_id, ad_id) VALUES (?, ?)", (user_id, ad_id)
        )
        log.info(f"Успешно добавлен ID объявления {ad_id} для пользователя {user_id}")
    except sqlite3.IntegrityError as e:
        log.warning(
            f"ID объявления {ad_id} для пользователя {user_id} уже существует: {e}"
        )
    except Exception as e:
        log.error(f"Ошибка при добавлении ID {ad_id} для пользователя {user_id}: {e}")


@db_connection(url)
def is_ad_seen(cursor: sqlite3.Cursor, user_id, ad_id):
    cursor.execute(
        "SELECT 1 FROM ads WHERE user_id = ? AND ad_id = ?", (user_id, ad_id)
    )
    return cursor.fetchone() is not None


@db_connection(url)
def replace_oldest_ads(cursor: sqlite3.Cursor, user_id, new_ad_ids):
    cursor.execute(
        "SELECT ad_id FROM ads WHERE user_id = ? ORDER BY rowid ASC", (user_id,)
    )
    current_ads = [row[0] for row in cursor.fetchall()]

    ads_to_keep = (current_ads + new_ad_ids)[-20:]  # Оставляем последние 20
    cursor.execute("DELETE FROM ads WHERE user_id = ?", (user_id,))

    cursor.executemany(
        "INSERT INTO ads (user_id, ad_id) VALUES (?, ?)",
        [(user_id, ad_id) for ad_id in ads_to_keep],
    )
    log.info(f"Обновлены последние 20 ID объявлений для пользователя {user_id}.")
