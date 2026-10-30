import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "bot.sqlite3")))
STARTED_AT = time.monotonic()
BOT_NAME = os.getenv("BOT_NAME", "DRACULA NOSFERA")
DEVELOPER = os.getenv("BOT_DEVELOPER", "MADO DEV")
CONTACT = os.getenv("BOT_CONTACT", "@MadoPhantomAI")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("dracula-nosfera")


def get_token() -> str:
    for key in ("TELEGRAM_BOT_TOKEN", "BOT_TOKEN", "TELEGRAM_TOKEN", "TOKEN"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    raise RuntimeError(
        "Token manquant : ajoute TELEGRAM_BOT_TOKEN dans les variables d'environnement."
    )


def get_admin_ids() -> set[int]:
    raw = ",".join(
        value for value in (
            os.getenv("OWNER_ID", ""),
            os.getenv("ADMIN_IDS", ""),
        ) if value.strip()
    )
    result: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if item.isdigit():
            result.add(int(item))
    return result


ADMIN_IDS = get_admin_ids()


def db_connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL
        )"""
    )
    connection.commit()
    return connection


def register_user(user) -> None:
    if user is None:
        return
    now = datetime.now(timezone.utc).isoformat()
    with db_connect() as connection:
        connection.execute(
            """INSERT INTO users(user_id, username, first_name, first_seen, last_seen)
               VALUES(?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username,
                 first_name=excluded.first_name,
                 last_seen=excluded.last_seen""",
            (user.id, user.username, user.first_name or "", now, now),
        )


def user_count() -> int:
    with db_connect() as connection:
        row = connection.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0]) if row else 0


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 Aide & commandes", callback_data="help"),
            InlineKeyboardButton("ℹ️ À propos", callback_data="about"),
        ],
        [
            InlineKeyboardButton("📜 Règles", callback_data="rules"),
            InlineKeyboardButton("✉️ Contact", callback_data="contact"),
        ],
    ])


WELCOME_TEXT = (
    "🧛‍♂️ <b>DRACULA NOSFERA</b>\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "Bienvenue {name} !\n\n"
    "Je suis ton assistant Telegram. Utilise les boutons ci-dessous "
    "ou envoie /help pour découvrir mes commandes.\n\n"
    "⚡ Développé par <b>" + DEVELOPER + "</b>"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    register_user(user)
    name = user.first_name if user else "utilisateur"
    await update.effective_message.reply_text(
        WELCOME_TEXT.format(name=name),
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    register_user(update.effective_user)
    await update.effective_message.reply_text(
        "🦇 <b>MENU PRINCIPAL</b>\nChoisis une rubrique :",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📚 <b>COMMANDES DISPONIBLES</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "/start — Démarrer le bot\n"
        "/menu — Ouvrir le menu\n"
        "/help — Afficher cette aide\n"
        "/ping — Vérifier la disponibilité\n"
        "/id — Afficher ton identifiant Telegram\n"
        "/info — Informations sur le bot\n"
        "/rules — Règles d'utilisation\n"
        "/contact — Contacter le développeur\n\n"
        "🔐 Commandes administrateur : /admin et /stats"
    )
    await update.effective_message.reply_text(text, parse_mode="HTML")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    elapsed = round(time.monotonic() - STARTED_AT, 2)
    await update.effective_message.reply_text(
        f"🟢 <b>En ligne</b>\nTemps de réponse : {elapsed}s",
        parse_mode="HTML",
    )


async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user:
        register_user(user)
        await update.effective_message.reply_text(
            f"🆔 Ton identifiant Telegram : <code>{user.id}</code>",
            parse_mode="HTML",
        )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        f"🧛‍♂️ <b>{BOT_NAME}</b>\n"
        "Assistant Telegram développé en Python.\n"
        f"Développeur : <b>{DEVELOPER}</b>\n"
        f"Contact : {CONTACT}",
        parse_mode="HTML",
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "📜 <b>RÈGLES D'UTILISATION</b>\n"
        "• Utilise le bot de manière respectueuse.\n"
        "• N'envoie pas d'informations personnelles sensibles.\n"
        "• Évite le spam et les messages abusifs.\n"
        "• Respecte les règles de Telegram.",
        parse_mode="HTML",
    )


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        f"✉️ Contact développeur : {CONTACT}\n"
        "N'envoie jamais ton mot de passe ni ton token de bot."
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.effective_message.reply_text("⛔ Accès réservé aux administrateurs.")
        return
    uptime = int(time.monotonic() - STARTED_AT)
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    await update.effective_message.reply_text(
        "🛡️ <b>PANNEAU ADMINISTRATEUR</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👥 Utilisateurs enregistrés : {user_count()}\n"
        f"⏱️ Temps actif : {hours}h {minutes}m {seconds}s\n"
        f"🆔 Ton ID : <code>{user.id}</code>\n"
        "🟢 État : opérationnel",
        parse_mode="HTML",
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.effective_message.reply_text("⛔ Accès réservé aux administrateurs.")
        return
    await update.effective_message.reply_text(
        f"📊 Utilisateurs enregistrés : {user_count()}"
    )


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    responses = {
        "help": (
            "📚 <b>COMMANDES</b>\n/start · /menu · /help · /ping · /id\n"
            "/info · /rules · /contact"
        ),
        "about": (
            f"🧛‍♂️ <b>{BOT_NAME}</b>\nAssistant Telegram Python.\n"
            f"Développeur : <b>{DEVELOPER}</b>\nContact : {CONTACT}"
        ),
        "rules": (
            "📜 <b>RÈGLES</b>\nRespecte les utilisateurs, évite le spam, "
            "protège tes informations personnelles et respecte Telegram."
        ),
        "contact": f"✉️ Contact développeur : {CONTACT}",
    }
    text = responses.get(query.data, "Rubrique inconnue.")
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=main_keyboard())


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Erreur pendant le traitement d'une mise à jour", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Une erreur est survenue. Réessaie dans quelques instants."
            )
        except Exception:
            logger.exception("Impossible d'envoyer le message d'erreur")


def main() -> None:
    token = get_token()
    db_connect()
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("id", user_id))
    app.add_handler(CommandHandler("info", about))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_router))
    app.add_error_handler(error_handler)

    logger.info("%s démarre en mode polling", BOT_NAME)
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
