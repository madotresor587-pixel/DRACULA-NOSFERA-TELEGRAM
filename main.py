import asyncio
import html
import logging
import os
import sqlite3
import time
from urllib.parse import quote
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
        "🔐 Commandes administrateur : /admin et /stats\n"
        "🧪 Simulations : /massreport NUMERO [NOMBRE], /banpem NUMERO [NOMBRE], /bantemp NUMERO [DUREE]\n"
        "✉️ Recours WhatsApp : /unban NUMERO [EXPLICATION]\n"
        "👥 Débannir un membre Telegram : /unban_group (répondre à son message ou donner son ID)\n"
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



async def moderation_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retourne (chat_id, cible_id, erreur). Cible par réponse ou ID numérique."""
    message = update.effective_message
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return None, None, "Cette commande fonctionne uniquement dans un groupe."
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif context.args and context.args[0].lstrip("-").isdigit():
        target_id = int(context.args[0])
    else:
        return chat.id, None, "Réponds au message de la personne ou indique son ID numérique. Exemple : /ban 123456789"
    return chat.id, target_id, None


async def check_moderator_rights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    actor = update.effective_user
    message = update.effective_message
    if not chat or not actor or not message:
        return False
    try:
        actor_member = await context.bot.get_chat_member(chat.id, actor.id)
        if actor_member.status not in ("administrator", "creator"):
            await message.reply_text("⛔ Seuls les administrateurs du groupe peuvent utiliser cette commande.")
            return False
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if bot_member.status != "administrator" or not getattr(bot_member, "can_restrict_members", False):
            await message.reply_text("⚠️ Je dois être administrateur du groupe avec le droit « Bannir des utilisateurs ».")
            return False
        return True
    except Exception:
        logger.exception("Vérification des droits de modération impossible")
        await message.reply_text("⚠️ Impossible de vérifier les droits. Vérifie que je suis administrateur du groupe.")
        return False


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, target_id, error = await moderation_target(update, context)
    if error:
        await update.effective_message.reply_text("⚠️ " + error)
        return
    if not await check_moderator_rights(update, context):
        return
    if target_id == context.bot.id:
        await update.effective_message.reply_text("Je ne peux pas me bannir moi-même.")
        return
    if target_id in ADMIN_IDS:
        await update.effective_message.reply_text("⛔ Cette personne est protégée comme administrateur du bot.")
        return
    try:
        target = await context.bot.get_chat_member(chat_id, target_id)
        if target.status in ("administrator", "creator"):
            await update.effective_message.reply_text("⛔ Impossible de bannir un administrateur ou le propriétaire du groupe.")
            return
        reason = " ".join(context.args[1:]).strip() if context.args and context.args[0].lstrip("-").isdigit() else ""
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_id)
        await update.effective_message.reply_text(
            f"🔨 Utilisateur <code>{target_id}</code> banni du groupe."
            + (f"\nMotif : {reason}" if reason else ""),
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Échec de /ban")
        await update.effective_message.reply_text("⚠️ Bannissement impossible. Vérifie mes droits et l'ID de la personne.")


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, target_id, error = await moderation_target(update, context)
    if error:
        await update.effective_message.reply_text("⚠️ " + error)
        return
    if not await check_moderator_rights(update, context):
        return
    if target_id == context.bot.id:
        await update.effective_message.reply_text("Cette action n'est pas nécessaire pour le bot.")
        return
    try:
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=target_id, only_if_banned=True)
        await update.effective_message.reply_text(
            f"♻️ Bannissement levé pour l'utilisateur <code>{target_id}</code>.\n"
            "Il peut rejoindre le groupe à nouveau via son lien d'invitation.",
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Échec de /unban")
        await update.effective_message.reply_text("⚠️ Débannissement impossible. Vérifie l'ID et mes droits.")


def normalize_phone(raw: str) -> str | None:
    value = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if value.startswith("+"):
        value = value[1:]
    if not value.isdigit() or not 8 <= len(value) <= 15:
        return None
    return "+" + value


async def run_report_simulation(update: Update, context: ContextTypes.DEFAULT_TYPE, label: str) -> None:
    message = update.effective_message
    if not context.args:
        await message.reply_text(f"Utilisation : /{label} NUMERO [NOMBRE]\nExemple : /{label} +2250700000000 500")
        return
    phone = normalize_phone(context.args[0])
    if not phone:
        await message.reply_text("Numéro invalide. Utilise le format international, par exemple +2250700000000.")
        return
    count = 500
    if len(context.args) > 1:
        try:
            count = int(context.args[1])
        except ValueError:
            await message.reply_text("Le nombre doit être un entier entre 1 et 500.")
            return
    if not 1 <= count <= 500:
        await message.reply_text("Choisis un nombre entre 1 et 500.")
        return

    status = await message.reply_text(
        "🧪 <b>MODE SIMULATION — aucun signalement réel n'est envoyé</b>\n"
        f"Numéro cible : <code>{phone}</code>\n"
        f"Opération : {label.upper()}\nProgression : 0/{count}",
        parse_mode="HTML",
    )
    for percent in (20, 40, 60, 80, 100):
        await asyncio.sleep(0.35)
        done = count * percent // 100
        try:
            await status.edit_text(
                "🧪 <b>MODE SIMULATION — aucun signalement réel n'est envoyé</b>\n"
                f"Numéro cible : <code>{phone}</code>\n"
                f"Opération : {label.upper()}\n"
                f"Progression : {done}/{count} ({percent}%)\n"
                "Traitement fictif des étapes de démonstration…",
                parse_mode="HTML",
            )
        except Exception:
            logger.exception("Impossible de mettre à jour la progression de simulation")
    await status.edit_text(
        "✅ <b>Simulation terminée</b>\n"
        f"Numéro : <code>{phone}</code>\n"
        f"Compteur simulé : {count}/{count}\n"
        "Aucun signalement n'a été transmis à WhatsApp et aucun compte n'a été banni.",
        parse_mode="HTML",
    )


async def massreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_report_simulation(update, context, "massreport")


async def banpem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_report_simulation(update, context, "banpem")


async def bantemp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.effective_message.reply_text(
            "Utilisation : /bantemp NUMERO DUREE\nExemple : /bantemp +2250700000000 24h"
        )
        return
    phone = normalize_phone(context.args[0])
    duration = context.args[1].strip()
    if not phone or not (1 <= len(duration) <= 12) or not all(c.isalnum() for c in duration):
        await update.effective_message.reply_text("Numéro ou durée invalide. Exemple : /bantemp +2250700000000 24h")
        return
    await update.effective_message.reply_text(
        "🧪 <b>BANNISSEMENT TEMPORAIRE — SIMULATION</b>\n"
        f"Numéro : <code>{phone}</code>\n"
        f"Durée fictive : <b>{duration}</b>\n"
        "Aucune restriction WhatsApp n'a été appliquée. Cette commande ne modifie aucun compte.",
        parse_mode="HTML",
    )


async def banperm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await run_report_simulation(update, context, "banperm")


async def check_whatsapp_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text(
            "Utilisation : /check NUMERO\\nExemple : /check +2250700000000"
        )
        return
    phone = normalize_phone(context.args[0])
    if not phone:
        await update.effective_message.reply_text(
            "Numéro invalide. Utilise le format international, par exemple +2250700000000."
        )
        return
    await update.effective_message.reply_text(
        "🔎 <b>Vérification du numéro</b>\\n"
        f"Numéro : <code>{phone}</code>\\n"
        "⚪ <b>Statut : impossible à déterminer depuis Telegram</b>\\n\\n"
        "WhatsApp ne fournit pas de service public permettant de vérifier le bannissement d'un compte à partir du seul numéro. "
        "Pour connaître le statut réel, ouvre WhatsApp avec ce numéro : si un avis de bannissement apparaît, suis "
        "« Demander un examen ». Si le compte s'ouvre normalement, aucun bannissement n'est signalé dans cette session. "
        "Cette commande ne prétend pas effectuer une vérification réelle.",
        parse_mode="HTML",
    )


async def unban_appeal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.effective_message.reply_text(
            "Utilisation : /unban NUMERO [EXPLICATION]\n"
            "Exemple : /unban +2250700000000 Mon compte semble avoir été bloqué par erreur."
        )
        return
    phone = normalize_phone(context.args[0])
    if not phone:
        await update.effective_message.reply_text("Numéro invalide. Utilise le format international, par exemple +2250700000000.")
        return
    explanation = " ".join(context.args[1:]).strip() or "Je pense que le blocage de mon compte est une erreur."
    subject = "Demande de réexamen de mon compte WhatsApp"
    body = (
        "Bonjour l'équipe WhatsApp,\n\n"
        f"Mon numéro WhatsApp est : {phone}\n\n"
        f"Explication : {explanation}\n\n"
        "Je vous remercie de bien vouloir réexaminer mon compte. "
        "Je reste disponible pour fournir les informations nécessaires.\n\n"
        "Cordialement."
    )
    await update.effective_message.reply_text(
        "✉️ <b>Projet de recours préparé</b>\n\n"
        f"<b>Objet :</b> {subject}\n\n"
        f"<b>Message :</b>\n{html.escape(body)}\n\n"
        "Ce texte n'a pas été envoyé. Pour un compte banni, WhatsApp recommande d'abord "
        "d'utiliser le bouton « Demander un examen » dans l'application. "
        "Tu peux aussi consulter le centre d'aide officiel : "
        '<a href="https://faq.whatsapp.com/465883178708358/?locale=fr_FR">À propos des bannissements</a> '
        "ou le <a href=\"https://www.whatsapp.com/contact?subject=messenger\">formulaire officiel de contact</a>.",
        parse_mode="HTML",
        disable_web_page_preview=True,
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
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban_group", unban_command))
    app.add_handler(CommandHandler("unban", unban_appeal_command))
    app.add_handler(CommandHandler("massreport", massreport_command))
    app.add_handler(CommandHandler("banpem", banpem_command))
    app.add_handler(CommandHandler("banperm", banperm_command))
    app.add_handler(CommandHandler("check", check_whatsapp_status))
    app.add_handler(CommandHandler("bantemp", bantemp_command))
    app.add_handler(CommandHandler("unban_appeal", unban_appeal_command))
    app.add_handler(CallbackQueryHandler(button_router))
    app.add_error_handler(error_handler)

    logger.info("%s démarre en mode polling", BOT_NAME)
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
