from db import *


def get_state_menu(user_id):
    return load_user_state(user_id=user_id)["is_url_menu"]


def update_state_menu(user_id, is_url_menu):
    return save_user_state_menu(user_id=user_id, in_url_menu=is_url_menu)
