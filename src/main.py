from datetime import datetime, time

import pytz
from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

from src.logger import get_logger
from src.repository.user import RepoUser
from src.settings import Settings
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
    if result is None or update.chat_member is None or update.effective_chat is None:
        return

    was_member, is_member = result
    member_username = update.chat_member.new_chat_member.user.username

    if not was_member and is_member:
        logger.info("New member {}", member_username)
        await update.effective_chat.send_message(
            f"Добро пожаловать в чат, {member_username}! Заполни, пожалуйста, [анкету](https://docs.google.com/spreadsheets/d/12RuhcpwpdIgIfKq5pVkbMcqRe3b6MAt8OtedMURg2Sg/edit#gid=0)",
            parse_mode=ParseMode.MARKDOWN,
        )
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
    if update.message.reply_to_message is None:
        await update.message.reply_text("Reply to message with menu")
        return
    dish_name = context.args[0]
    message_url = f"https://t.me/c/1563220312/{update.message.reply_to_message.message_id}"
    await context.bot.send_message(
        settings.menu_channel_id, text=f"{message_url} {dish_name}", parse_mode=ParseMode.MARKDOWN
    )
    await update.message.reply_text("Menu sent")


def main() -> None:
    """Start the bot."""
    logger.info("start bot")
    time_zone = pytz.timezone(settings.timezone)
    application = Application.builder().token(settings.token).build()

    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(CommandHandler("menu", send_menu))
    application.add_handler(CommandHandler("ping", ping))

    application.job_queue.run_daily(sync_birthdays_table, time=time(10, 0, tzinfo=time_zone))
    application.job_queue.run_daily(check_birthdays, time=time(8, 0, tzinfo=time_zone))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
