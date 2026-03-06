import asyncio
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import BOT_TOKEN, MONO_PAYMENT_URL, OWNER_CHAT_ID
from .users import register_user
from .users import get_users_count
from .users import get_all_user_ids
from .keyboards import services_menu_kb, CB_SERVICE
from .services import get_service
from .forms import (
    start_form,
    handle_form_text,
    cancel_form,
    handle_non_text_during_form,
)

from .stats import inc_stat, format_stats

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BROADCAST_MODE = {}
BOT_PAUSED = False


def service_card_kb(service_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Реквізити", callback_data=f"pay:{service_id}")],
        [InlineKeyboardButton("🏠 Назад в головне меню", callback_data="back:services")],
    ])


def payment_kb(service_id: str) -> InlineKeyboardMarkup:
    rows = []

    if MONO_PAYMENT_URL:
        rows.append([InlineKeyboardButton("💳 Перейти до реквізитів", url=MONO_PAYMENT_URL)])

    rows.append([InlineKeyboardButton("✅ Я заповнила(в)", callback_data=f"paid:{service_id}")])
    rows.append([InlineKeyboardButton("🏠 Назад в головне меню", callback_data="back:services")])

    return InlineKeyboardMarkup(rows)


async def safe_edit_message(
    query,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None
):
    reply_markup = reply_markup or InlineKeyboardMarkup([])
    msg = query.message

    try:
        if getattr(msg, "photo", None):
            await query.edit_message_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
        return True
    except Exception as e:
        logger.exception("safe_edit_message failed: %s", e)
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("form", None)
    register_user(update.effective_user)
    inc_stat("start")

    if BOT_PAUSED:
        await update.message.reply_text(
            "⏸ Запис тимчасово закрито.\n\nСпробуйте завтра."
        )
        return

    try:
        with open("assets/start.mp4", "rb") as animation:
            await update.message.reply_animation(
                animation=animation,
                caption=" ",
                reply_markup=services_menu_kb(),
                protect_content=True,
            )
    except Exception:
        await update.message.reply_text(
            " ",
            reply_markup=services_menu_kb(),
            protect_content=True,
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

<<<<<<< HEAD
    if not OWNER_CHAT_ID or user_id != str(OWNER_CHAT_ID):
        await update.message.reply_text("УПС))) у вас немає доступу до цієї команди.")
=======
    if str(user_id) != str(OWNER_CHAT_ID):
>>>>>>> 7bab5c3 (update bot: admin panel, broadcast image, fixes)
        return

    await update.message.reply_text(format_stats())


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if str(user_id) != str(OWNER_CHAT_ID):
        return

    count = get_users_count()

    await update.message.reply_text(
        f"👥 Користувачів бота: {count}"
    )


async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_PAUSED

    user_id = str(update.effective_user.id)

    if str(user_id) != str(OWNER_CHAT_ID):
        return

    BOT_PAUSED = True

    await update.message.reply_text(
        "⏸ Бот поставлено на паузу.\n\nКористувачі тимчасово не можуть користуватися ботом."
    )


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_PAUSED

    user_id = str(update.effective_user.id)

    if str(user_id) != str(OWNER_CHAT_ID):
        return

    BOT_PAUSED = False

    await update.message.reply_text(
        "▶️ Бот знову активний."
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if str(user_id) != str(OWNER_CHAT_ID):
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton("👥 Користувачі", callback_data="admin:users")],
        [InlineKeyboardButton("📨 Розсилка", callback_data="admin:broadcast")],
        [InlineKeyboardButton("⏸ Пауза", callback_data="admin:pause")],
        [InlineKeyboardButton("▶️ Запуск", callback_data="admin:resume")],
    ])

    await update.message.reply_text(
        "🔐 Адмін-панель",
        reply_markup=kb,
    )


async def admin_panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_PAUSED

    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)

    if str(user_id) != str(OWNER_CHAT_ID):
        return

    action = query.data

    if action == "admin:stats":
        await query.edit_message_text(format_stats())
        return

    if action == "admin:users":
        count = get_users_count()
        await query.edit_message_text(f"👥 Користувачів бота: {count}")
        return

    if action == "admin:broadcast":
        BROADCAST_MODE[user_id] = True
        await query.edit_message_text(
            "📨 Напишіть текст (повідомлення) розсилки.\n\n"
            "Він буде відправлений всім користувачам бота."
        )
        return

    if action == "admin:pause":
        BOT_PAUSED = True
        await query.edit_message_text("⏸ Бот поставлено на паузу.")
        return

    if action == "admin:resume":
        BOT_PAUSED = False
        await query.edit_message_text("▶️ Бот знову активний.")
        return


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if str(user_id) != str(OWNER_CHAT_ID):
        return

    BROADCAST_MODE[user_id] = True

    await update.message.reply_text(
        "📨 Напишіть текст (повідомлення) розсилки.\n\n"
        "Він буде відправлений всім користувачам бота."
    )


async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in BROADCAST_MODE:
        return

    if str(user_id) != str(OWNER_CHAT_ID):
        BROADCAST_MODE.pop(user_id, None)
        return

    BROADCAST_MODE.pop(user_id, None)

    text = update.message.text
    users = get_all_user_ids()

    sent = 0

    for uid in users:
        try:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✨ Записатися на консультацію", callback_data="back:services")]
            ])

            try:
                with open("assets/broadcast.jpg", "rb") as photo:
                    await context.bot.send_photo(
                        chat_id=uid,
                        photo=photo,
                        caption=text,
                        reply_markup=kb,
                        protect_content=True,
                    )
            except Exception:
                await context.bot.send_message(
                    chat_id=uid,
                    text=text,
                    reply_markup=kb,
                    protect_content=True,
                )

            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await update.message.reply_text(
        f"✅ Розсилку завершено.\n\nОтримали: {sent} користувачів."
    )


async def handle_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id in BROADCAST_MODE:
        await handle_broadcast(update, context)
        return

    if context.user_data.get("form"):
        await handle_form_text(update, context)
        return

    await update.effective_message.reply_text("На даному етапі введення тексту недоступне.")


async def on_service_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, service_id = query.data.split(":", 1)
    service = get_service(service_id)

    if not service:
        await safe_edit_message(query, "Елемент не знайдено.")
        return

    inc_stat("service_open")

    title = service["title"]
    price = service["price_uah"]
    image = service.get("image")

    caption = (
        f"✨ <b>{title}</b>\n\n"
        f"💳 💴 <b>{price} грн</b>\n"
        f"⬇️"
    )

    if not image:
        ok = await safe_edit_message(query, caption, service_card_kb(service_id))
        if ok:
            return

    try:
        await query.message.delete()
    except Exception:
        pass

    if image:
        try:
            with open(image, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=caption,
                    reply_markup=service_card_kb(service_id),
                    parse_mode="HTML",
                    protect_content=True,
                )
            return
        except FileNotFoundError:
            pass

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=caption,
        reply_markup=service_card_kb(service_id),
        parse_mode="HTML",
        protect_content=True,
    )


async def on_back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    context.user_data.pop("form", None)

    ok = await safe_edit_message(
        query,
        "✨",
        services_menu_kb(),
    )
    if ok:
        return

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="✨",
        reply_markup=services_menu_kb(),
        parse_mode="HTML",
    )


async def on_pay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, service_id = query.data.split(":", 1)
    service = get_service(service_id)

    if not service:
        await safe_edit_message(query, "Елемент не знайдено.")
        return

    inc_stat("requisites_open")

    title = service["title"]
    price = service["price_uah"]

    text = (
        f"✨ <b>{title}</b>\n"
        f"💳 💴 <b>{price} грн</b>\n\n"
        "Для отримання інформації перейдіть далі.\n"
        "Після заповнення натисніть кнопку <b>\"Я заповнила(в)\"</b>."
    )

    await safe_edit_message(query, text, payment_kb(service_id))


async def on_paid_start_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    _, service_id = query.data.split(":", 1)
    inc_stat("form_started")

    await safe_edit_message(
        query,
        "✅ <b>Перехід далі</b>\n\nЗаповніть дані нижче.",
        InlineKeyboardMarkup([]),
    )

    await start_form(update, context, service_id)


async def on_form_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cancel_form(update, context)


async def on_text_before_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("form"):
        return
    await update.effective_message.reply_text("На даному етапі введення тексту недоступне.")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error: %s", context.error)


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty.")

    asyncio.set_event_loop(asyncio.new_event_loop())

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("resume", resume_command))
    app.add_handler(CommandHandler("admin", admin_command))

    app.add_handler(CallbackQueryHandler(on_service_click, pattern=f"^{CB_SERVICE}:"))
    app.add_handler(CallbackQueryHandler(on_back_to_services, pattern=r"^back:services$"))
    app.add_handler(CallbackQueryHandler(on_pay, pattern=r"^pay:"))
    app.add_handler(CallbackQueryHandler(on_paid_start_form, pattern=r"^paid:"))
    app.add_handler(CallbackQueryHandler(on_form_cancel, pattern=r"^form:cancel$"))
    app.add_handler(CallbackQueryHandler(admin_panel_click, pattern=r"^admin:"))

    # текст під час активної форми
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_router))

    # будь-які не-текстові повідомлення
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND, handle_non_text_during_form))

    app.add_error_handler(on_error)

    logger.info("Bot started (polling).")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":

    main()
