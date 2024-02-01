import random
from datetime import datetime, time

import pytz
from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.llm import LLM
from src.logger import get_logger
from src.repository.user import RepoUser
from src.settings import Settings
from src.texts import HELP_TEXT, JOIN_MESSAGE, MENU_TEXT, SUPPORTIVE_PHRASES
from src.utils import update_table

logger = get_logger(__name__)
settings = Settings()


async def check_birthdays(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if there are any birthdays today and send a message to the chat."""
    logger.info("Checking birthdays")
    try:
        birthday_users = await RepoUser.get_users_with_birthday(datetime.now(pytz.timezone(settings.timezone)))
    except Exception as e:
        logger.exception(e)
        await context.bot.send_message(settings.admin_chat_id, text=f"Error: {e}")
        return
    if len(birthday_users) == 0:
        await context.bot.send_message(settings.admin_chat_id, text="No birthdays today")
        return
    for user in birthday_users:
        await context.bot.send_message(
            settings.chat_id,
            text=f"Самое время поздравить {user.username} с Днём Рождения!🎉✨",  # noqa
        )


async def send_horoscope(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send horoscope to the chat."""
    logger.info("Sending horoscope")
    try:
        horoscope = LLM.generate_horoscope()
    except Exception as e:
        logger.exception(e)
        await context.bot.send_message(settings.admin_chat_id, text=f"Error: {e}")
        return
    await context.bot.send_message(
        settings.chat_id,
        text=horoscope,
        parse_mode=ParseMode.MARKDOWN,
    )


def extract_status_change(chat_member_update: ChatMemberUpdated) -> tuple[bool, bool] | None:
    """
    Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    logger.info("Greeting chat members")
    if update.chat_member is None:
        return
    result = extract_status_change(update.chat_member)
    if (
        result is None
        or update.chat_member is None
        or update.effective_chat is None
        or update.effective_chat.id != settings.chat_id
    ):
        return

    was_member, is_member = result
    member_username = (
        "@" + update.chat_member.new_chat_member.user.username
        if update.chat_member.new_chat_member.user.username is not None
        else update.chat_member.new_chat_member.user.full_name
    )

    logger.info(
        "used_memer username {} real username {} fullname {}",
        member_username,
        update.chat_member.new_chat_member.user.username,
        update.chat_member.new_chat_member.user.full_name,
    )

    if not was_member and is_member:
        await update.effective_chat.send_message(
            JOIN_MESSAGE.format(member_username),
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info(f"New member {member_username}")
    elif was_member and not is_member:
        await context.bot.send_message(
            settings.admin_chat_id,
            text=f"{member_username} покинул чат",
        )


async def sync_birthdays_table(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sync birthdays table with database."""
    logger.info("Syncing birthdays table with database")
    try:
        birthday_table = await update_table(settings.sheet_id, settings.sheet_name)
    except Exception as e:
        logger.exception(e)
        await context.bot.send_message(settings.admin_chat_id, text=f"Error: {e}")
        return
    birthday_table = birthday_table.dropna(subset=["Ник в тг", "Имя", "День Рождения"])
    usernames = birthday_table["Ник в тг"].tolist()
    nicknames = birthday_table["Имя"].tolist()
    birthdays = birthday_table["День Рождения"].tolist()
    try:
        (users, removed_users) = await RepoUser.create_or_update_users(usernames, nicknames, birthdays)
    except Exception as e:
        logger.exception(e)
        await context.bot.send_message(settings.admin_chat_id, text=f"Error: {e}")
        return
    logger.info(
        "Created {} users: {}. Removed {} users from database: {}".format(
            len(users),
            ", ".join(user.username for user in users),
            len(removed_users),
            ", ".join(user.username for user in removed_users),
        )
    )
    await context.bot.send_message(settings.admin_chat_id, text=f"Synced table. Created {len(users)} users")


async def good_morning(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(settings.chat_id, text="Доброе утро, чач!")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping bot."""
    if update.message is None:
        return
    logger.info(f"Ping {update.message.chat.id}")
    await update.message.reply_text("Pong")


async def send_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send menu to channel."""
    logger.info("Sending menu")
    if update.message is None:
        return
    if update.message.reply_to_message is None or context.args is None or len(context.args) == 0:
        await update.message.reply_text("Reply to message with menu")
        return

    dish_name = " ".join(context.args)
    message_url = f"https://t.me/c/1563220312/{update.message.reply_to_message.message_id}"
    await context.bot.send_message(
        settings.menu_channel_id, text=f"{message_url} {dish_name}", parse_mode=ParseMode.MARKDOWN
    )
    await update.message.reply_text("Menu sent")


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        MENU_TEXT,
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        HELP_TEXT,
    )


async def send_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if update.message.chat.id != settings.chat_id:
        return
    if update.message.message_id % 50 != 0:
        return

    await update.message.reply_text(SUPPORTIVE_PHRASES[random.randint(0, len(SUPPORTIVE_PHRASES) - 1)])


def add_handlers(application: Application) -> None:
    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(CommandHandler("menu", send_menu))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("show_menu", show_menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_support_message))


def add_jobs(application: Application, time_zone_str: str) -> None:
    time_zone = pytz.timezone(time_zone_str)
    if application.job_queue is None:
        raise ValueError("Job queue is None")
    application.job_queue.run_daily(sync_birthdays_table, time=time(8, tzinfo=time_zone))
    application.job_queue.run_daily(check_birthdays, time=time(10, tzinfo=time_zone))
    application.job_queue.run_daily(good_morning, time=time(8, tzinfo=time_zone))
    application.job_queue.run_daily(send_horoscope, time=time(9, tzinfo=time_zone))


def main() -> None:
    """Start the bot."""
    logger.info("start bot")

    application = Application.builder().token(settings.token).build()

    add_handlers(application)
    add_jobs(application, settings.timezone)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
