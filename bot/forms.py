from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .services import get_service
from .config import OWNER_CHAT_ID, OWNER_TG_LINK
from .stats import inc_stat

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
REQUESTS_FILE = DATA_DIR / "requests.jsonl"

DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def v_nonempty(text: str) -> Tuple[bool, str]:
    t = text.strip()
    if not t:
        return False, "Будь ласка, введіть значення."
    return True, t


def v_date_ddmmyyyy(text: str) -> Tuple[bool, str]:
    t = text.strip()
    if not DATE_RE.match(t):
        return False, "Дата має бути у форматі дд.мм.рррр."
    try:
        datetime.strptime(t, "%d.%m.%Y")
    except ValueError:
        return False, "Схоже, дата некоректна. Спробуйте ще раз."
    return True, t


def v_time_hhmm(text: str) -> Tuple[bool, str]:
    t = text.strip()
    if not TIME_RE.match(t):
        return False, "Час має бути у форматі гг:хх."
    hh, mm = t.split(":")
    try:
        h = int(hh)
        m = int(mm)
    except Exception:
        return False, "Час має бути у форматі гг:хх."
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return False, "Час некоректний."
    return True, t


@dataclass
class Step:
    key: str
    prompt: str
    validator: Callable[[str], Tuple[bool, str]]


def build_steps(service_id: str) -> List[Step]:
    service = get_service(service_id) or {}
    form_type = service.get("form_type", "birth")

    name_step = Step("client_name", "Напишіть, будь ласка, ваше ім'я:", v_nonempty)

    if form_type == "birth":
        return [
            name_step,
            Step("birth_date", "Ваша дата народження (дд.мм.рррр):", v_date_ddmmyyyy),
            Step("birth_time", "Ваш час народження (гг:хх):", v_time_hhmm),
            Step("birth_place", "Місце народження (місто, країна):", v_nonempty),
        ]

    if form_type == "child_birth":
        return [
            name_step,
            Step("child_name", "Ім'я дитини:", v_nonempty),
            Step("child_birth_date", "Дата народження дитини (дд.мм.рррр):", v_date_ddmmyyyy),
            Step("child_birth_time", "Час народження дитини (гг:хх):", v_time_hhmm),
            Step("child_birth_place", "Місце народження дитини (місто, країна):", v_nonempty),
        ]

    if form_type == "tarot":
        return [
            name_step,
            Step("situation", "Опишіть ситуацію:", v_nonempty),
            Step("question", "Сформулюйте питання/сфери:", v_nonempty),
        ]

    if form_type == "consult":
        return [
            name_step,
            Step("birth_date", "Ваша дата народження (дд.мм.рррр):", v_date_ddmmyyyy),
            Step("preferred_time", "Зручний час для консультації:", v_nonempty),
            Step("topic", "Коротко опишіть тему консультації:", v_nonempty),
        ]

    return [name_step, Step("details", "Опишіть деталі запиту:", v_nonempty)]


def form_action_kb(show_edit: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if show_edit:
        rows.append([InlineKeyboardButton("✏️ Редагувати заповнення", callback_data="form:cancel")])
    rows.append([InlineKeyboardButton("🏠 Назад в головне меню", callback_data="back:services")])
    return InlineKeyboardMarkup(rows)


def after_submit_kb() -> InlineKeyboardMarkup:
    rows = []
    if OWNER_TG_LINK:
        rows.append([InlineKeyboardButton("💬 Перейти в мій Telegram", url=OWNER_TG_LINK)])
    rows.append([InlineKeyboardButton("🏠 Назад в головне меню", callback_data="back:services")])
    return InlineKeyboardMarkup(rows)


async def clear_last_prompt_buttons(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    form = context.user_data.get("form")
    if not form:
        return

    last_prompt_message_id = form.get("last_prompt_message_id")
    if not last_prompt_message_id:
        return

    try:
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=last_prompt_message_id,
            reply_markup=None,
        )
    except Exception:
        pass


async def send_form_prompt(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    show_edit: bool = False,
) -> None:
    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=form_action_kb(show_edit=show_edit),
    )
    context.user_data["form"]["last_prompt_message_id"] = msg.message_id


async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id: str) -> None:
    service = get_service(service_id)
    if not service:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Елемент не знайдено.")
        return

    steps = build_steps(service_id)
    context.user_data["form"] = {
        "service_id": service_id,
        "step_idx": 0,
        "answers": {},
        "started_at": datetime.utcnow().isoformat(),
        "last_prompt_message_id": None,
    }

        if context.user_data["form"].get("last_prompt_message_id"):
        return

    await send_form_prompt(
        context=context,
        chat_id=update.effective_chat.id,
        text=steps[0].prompt,
        show_edit=False,
    )


async def cancel_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    old_form = context.user_data.get("form") or {}
    service_id = old_form.get("service_id")

    if not service_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Немає активного заповнення.",
        )
        return

    await clear_last_prompt_buttons(context, update.effective_chat.id)

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    steps = build_steps(service_id)
    context.user_data["form"] = {
        "service_id": service_id,
        "step_idx": 0,
        "answers": {},
        "started_at": datetime.utcnow().isoformat(),
        "last_prompt_message_id": None,
    }

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Заповнення розпочато спочатку.",
    )

    await send_form_prompt(
        context=context,
        chat_id=update.effective_chat.id,
        text=steps[0].prompt,
        show_edit=False,
    )


async def handle_form_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    form = context.user_data.get("form")

    if not form:
        await update.effective_message.reply_text("На даному етапі введення тексту недоступне.")
        return

    service_id = form["service_id"]
    steps = build_steps(service_id)
    idx = int(form.get("step_idx", 0))

    step = steps[idx]
    ok, value_or_msg = step.validator(update.message.text)

    if not ok:
        await update.effective_message.reply_text(value_or_msg)
        return

    form["answers"][step.key] = value_or_msg
    form["step_idx"] = idx + 1

    await clear_last_prompt_buttons(context, update.effective_chat.id)

    if form["step_idx"] < len(steps):
        next_step = steps[form["step_idx"]]
        await send_form_prompt(
            context=context,
            chat_id=update.effective_chat.id,
            text=next_step.prompt,
            show_edit=True,
        )
        return

    await finalize_form(update, context)


async def handle_non_text_during_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("form"):
        await update.effective_message.reply_text("На даному етапі доступне лише введення тексту.")
    else:
        await update.effective_message.reply_text("На даному етапі введення недоступне.")


def build_owner_message(payload: Dict) -> str:
    service = payload.get("service", {})
    a = payload.get("answers", {})
    tg = payload.get("telegram", {})

    lines = [
        "✨ НОВА ЗАЯВКА",
        "",
        f"🔮 Напрям:",
        f"{service.get('title', '—')}",
        "",
        "👤 Ім'я:",
        f"{a.get('client_name', '—')}",
        "",
        "📅 Дата:",
        f"{a.get('birth_date', a.get('child_birth_date', '—'))}",
        "",
        "⏰ Час:",
        f"{a.get('birth_time', a.get('child_birth_time', '—'))}",
        "",
        "📍 Місце:",
        f"{a.get('birth_place', a.get('child_birth_place', '—'))}",
        "",
        "💬 Telegram:",
        f"@{tg.get('username')}" if tg.get("username") else "немає username",
    ]

    return "\n".join(lines)

    order = [
        ("client_name", "Ім'я"),
        ("birth_date", "Дата народження"),
        ("birth_time", "Час народження"),
        ("birth_place", "Місце народження"),
        ("child_name", "Ім'я дитини"),
        ("child_birth_date", "Дата народження дитини"),
        ("child_birth_time", "Час народження дитини"),
        ("child_birth_place", "Місце народження дитини"),
        ("situation", "Ситуація"),
        ("question", "Питання/сфери"),
        ("preferred_time", "Зручний час"),
        ("topic", "Тема консультації"),
        ("details", "Деталі"),
    ]

    for key, label in order:
        if key in a:
            lines.append(f"- {label}: {a[key]}")

    lines.extend([
        "",
        "Telegram клієнта:",
        f"- id: {tg.get('user_id', '—')}",
        f"- username: @{tg['username']}" if tg.get("username") else "- username: немає",
        f"- name: {tg.get('full_name', '—')}",
    ])

    return "\n".join(lines)


async def finalize_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    form = context.user_data.get("form") or {}
    service_id = form.get("service_id")
    service = get_service(service_id) if service_id else None

    await clear_last_prompt_buttons(context, update.effective_chat.id)

    user = update.effective_user
    payload = {
        "created_at": datetime.utcnow().isoformat(),
        "service": service,
        "answers": form.get("answers", {}),
        "telegram": {
            "user_id": user.id if user else None,
            "username": getattr(user, "username", None),
            "full_name": f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip(),
        },
        "chat_id": update.effective_chat.id if update.effective_chat else None,
    }

    with REQUESTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    if OWNER_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=int(OWNER_CHAT_ID), text=build_owner_message(payload))
            logger.info("Заявку відправлено OWNER_CHAT_ID=%s", OWNER_CHAT_ID)
        except Exception as e:
            logger.exception("Не вдалося відправити заявку OWNER_CHAT_ID=%s: %s", OWNER_CHAT_ID, e)
    else:
        logger.error("OWNER_CHAT_ID порожній")

    context.user_data.pop("form", None)

    inc_stat("form_completed")

    text = (
        "✨ Дякую!\n\n"
        "Я отримала ваші дані.\n"
        "Зв'яжусь з вами у Telegram найближчим часом."
    )
    await update.effective_message.reply_text(text, reply_markup=after_submit_kb())
