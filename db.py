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
    # Проверка на существование колонки user_id в таблице ads (миграция, так изменялась после первого создания)
    check_column_user_id()

    # Создание таблицы user_urls, если она отсутствует
    create_userurls_table()
    # Проверка на существование колонки name в таблице user_urls (миграция, так изменялась после первого создания)
    check_column_urlname()

    # Создание таблицы состояния ссылок
    create_userstate_table()
    # Добавляем новые колонки в user_state, если их ещё нет (миграция, так изменялась после первого создания)
    check_columns_usersates()
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
def check_column_user_id(cursor: sqlite3.Cursor):
    cursor.execute("PRAGMA table_info(ads)")
    columns = [info[1] for info in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE ads ADD COLUMN user_id INTEGER")
        log.info("Добавлена колонка user_id в таблицу ads.")


@db_connection(url)
def check_columns_usersates(cursor: sqlite3.Cursor):

    cursor.execute("PRAGMA table_info(user_state)")
    columns = [info[1] for info in cursor.fetchall()]
    if "in_url_menu" not in columns:
        cursor.execute(
            "ALTER TABLE user_state ADD COLUMN in_url_menu BOOLEAN DEFAULT False"
        )

    if "previous_menu" not in columns:
        cursor.execute(
            "ALTER TABLE user_state ADD COLUMN previous_menu TEXT DEFAULT NULL"
        )
        log.info("Добавлена колонка previous_menu в таблицу user_state.")


@db_connection(url)
def check_column_urlname(cursor: sqlite3.Cursor):
    cursor.execute("PRAGMA table_info(user_urls)")
    columns = [info[1] for info in cursor.fetchall()]
    if "name" not in columns:
        cursor.execute("ALTER TABLE user_urls ADD COLUMN name TEXT")
        log.info("Добавлена колонка name в таблицу user_urls.")


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
        """
    CREATE TABLE IF NOT EXISTS user_state (
        user_id INTEGER PRIMARY KEY,
        url TEXT,
        is_running BOOLEAN
    )
    """
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
    if len(res) == 0:
        return 3
    return res[0]


@db_connection(url)
def get_user_urls(cursor: sqlite3.Cursor, user_id):
    cursor.execute("SELECT url, name FROM user_urls WHERE user_id = ?", (user_id,))
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
        f"SELECT is_running FROM user_state WHERE user_id = {user_id} AND url = '{url}'"
    )
    result = bool(cursor.fetchone())
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
def save_user_state(cursor: sqlite3.Cursor, user_id, url, is_running):
    cursor.execute(
        "INSERT OR REPLACE INTO user_state (user_id, url, is_running) VALUES (?, ?, ?)",
        (
            user_id,
            url,
            is_running,
        ),
    )


@db_connection(url)
def save_user_state_menu(cursor: sqlite3.Cursor, user_id, in_url_menu=False):
    global log
    log.info(f"Сохранение состояния пользователя {user_id}: in_url_menu={in_url_menu}")
    cursor.execute(
        """
        INSERT INTO user_state (user_id, in_url_menu)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET in_url_menu = ?
    """,
        (user_id, in_url_menu, in_url_menu),
    )


@db_connection(url)
def save_user_state_running(cursor: sqlite3.Cursor, user_id, url, is_running):
    cursor.execute(
        f"UPDATE user_state SET is_running = {is_running} WHERE user_id = {user_id} AND url = '{url}'",
    )


@db_connection(url)
def save_user_state_url(cursor: sqlite3.Cursor, user_id, url):
    cursor.execute("UPDATE user_state SET url = ? WHERE user_id = ?", (url, user_id))


@db_connection(url)
def load_user_state(cursor: sqlite3.Cursor, user_id, url_name):
    """Загружает состояние пользователя."""
    cursor.execute(
        """
        SELECT user_id, url, is_running, in_url_menu FROM user_state WHERE user_id = ? AND name = ?
    """,
        (user_id, url_name),
    )
    row = cursor.fetchone()
    if row:
        return {row[0]: {"url": row[1], "is_running": row[2], "in_url_menu": row[3]}}
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


@db_connection(url)
def reset_user_menu_state(cursor: sqlite3.Cursor, user_id):
    cursor.execute(
        "UPDATE user_state SET in_url_menu = False WHERE user_id = ?", (user_id,)
    )


@db_connection(url)
def save_user_previous_menu(cursor: sqlite3.Cursor, user_id, previous_menu):
    cursor.execute(
        "UPDATE user_state SET previous_menu = ? WHERE user_id = ?",
        (previous_menu, user_id),
    )


@db_connection(url)
def save_user_state_menu(cursor: sqlite3.Cursor, user_id, in_url_menu=False):
    log.info(f"Сохранение состояния пользователя {user_id}: in_url_menu={in_url_menu}")
    cursor.execute(
        """
        INSERT INTO user_state (user_id, in_url_menu)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET in_url_menu = ?
    """,
        (user_id, in_url_menu, in_url_menu),
    )
