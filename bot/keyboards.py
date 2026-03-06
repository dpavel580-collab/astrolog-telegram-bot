from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .services import SERVICES

CB_SERVICE = "service"


def services_menu_kb() -> InlineKeyboardMarkup:
    rows = []

    for s in SERVICES:
        text = f'{s["title"]}'
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"{CB_SERVICE}:{s['id']}"
            )
        ])

    return InlineKeyboardMarkup(rows)