import html
import json
import random
import traceback
from datetime import datetime, time

import pytz
from llm import LLM
from logger import get_logger
from read_recipes import parse_recipes
from repository import RecipiesRepo, UserRepo
from settings import Settings
from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)
from texts import HELP_TEXT, JOIN_MESSAGE, MENU_TEXT, SUPPORTIVE_PHRASES, USER_SUPPORTIVE
from utils import escape_markdown, update_table

logger = get_logger(__name__)
settings = Settings()


async def check_birthdays(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if there are any birthdays today and send a message to the chat."""
    logger.info("Checking birthdays")
    birthday_users = await UserRepo.get_users_with_birthday(datetime.now(pytz.timezone(settings.timezone)))

    if len(birthday_users) == 0:
        await context.bot.send_message(settings.admin_chat_id, text="No birthdays today")
        return
    for user in birthday_users:
        await context.bot.send_message(
            settings.chat_id,
            text=f"Самое время поздравить {user.username} с Днём Рождения!🎉✨",
        )


async def send_horoscope(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send horoscope to the chat."""
    logger.info("Sending horoscope")
    horoscope = LLM.generate_horoscope()

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
    allowed_statuses = [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ]
    was_member = old_status in allowed_statuses or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in allowed_statuses or (new_status == ChatMember.RESTRICTED and new_is_member is True)

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
    full_name = update.chat_member.new_chat_member.user.full_name
    username = update.chat_member.new_chat_member.user.username

    member_username = "@" + username if username is not None else full_name
    member_username = escape_markdown(member_username)

    logger.info(f"used_memer username {member_username} real username {username} fullname {full_name}")

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

    birthday_table = await update_table(settings.sheet_id, settings.sheet_name)
    usernames = birthday_table["Ник в тг"].tolist()
    nicknames = birthday_table["Имя"].tolist()
    birthdays = birthday_table["День Рождения"].tolist()

    users, removed_users = await UserRepo.create_or_update_users(usernames, nicknames, birthdays)
    logger.info(
        "Created {} users: {}. Removed {} users from database: {}".format(
            len(users),
            ", ".join(user.username for user in users),
            len(removed_users),
            ", ".join(user.username for user in removed_users),
        )
    )
    await context.bot.send_message(settings.admin_chat_id, text=f"Synced table. Created {len(users)} users")


async def find_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Find recipe")
    if context.args is None or len(context.args) == 0:
        await update.message.reply_text("Введите название блюда")
        return

    dish_name = " ".join(context.args)
    logger.info(f"Search recipe by name {dish_name}")
    recipes = await RecipiesRepo.search_recipe_by_name(dish_name)
    if len(recipes) == 0:
        await update.message.reply_text("Рецепт не найден")
        return
    response_text = "\n".join(rf"\- [{escape_markdown(recipe.name)}]({recipe.link})" for recipe in recipes)
    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping bot."""
    if update.message is None:
        return
    logger.info(f"Ping {update.message.chat.id}")
    await update.message.reply_text("Pong")


async def create_recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Create a recipe from a message and send it to the menu channel.
    """
    logger.info(f"Create recipe {update.message.chat.id}")
    if update.message is None:
        return
    if update.message.reply_to_message is None or context.args is None or len(context.args) == 0:
        await update.message.reply_text("Введите название блюда и его рецепт в ответ на сообщение с рецептом")
        return

    dish_name = " ".join(context.args)
    message_url = f"https://t.me/c/1563220312/{update.message.reply_to_message.message_id}"
    await context.bot.send_message(
        settings.menu_channel_id, text=f"{message_url} {dish_name}", parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Menu sent {message_url} {dish_name}")
    await RecipiesRepo.add_recipe(dish_name, message_url)
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
    elif update.message.message_id % 250 == 0:
        await update.message.reply_text(USER_SUPPORTIVE[random.randint(0, len(USER_SUPPORTIVE) - 1)])
        return
    await update.message.reply_text(SUPPORTIVE_PHRASES[random.randint(0, len(SUPPORTIVE_PHRASES) - 1)])


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/errorhandlerbot.py
    logger.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    await context.bot.send_message(settings.admin_chat_id, text=message, parse_mode=ParseMode.HTML)


# async def good_morning(context: ContextTypes.DEFAULT_TYPE) -> None:
#     await context.bot.send_message(settings.chat_id, text="Доброе утро, чач!")


def add_handlers(application: Application) -> None:
    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(CommandHandler("menu", create_recipe))
    application.add_handler(CommandHandler("add_recipe", create_recipe))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("show_menu", show_menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search_recipe", find_recipe))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_support_message))


def add_jobs(application: Application, time_zone_str: str) -> None:
    time_zone = pytz.timezone(time_zone_str)
    if application.job_queue is None:
        raise ValueError("Job queue is None")
    application.job_queue.run_daily(sync_birthdays_table, time=time(8, tzinfo=time_zone))
    application.job_queue.run_daily(check_birthdays, time=time(9, tzinfo=time_zone))
    # application.job_queue.run_daily(good_morning, time=time(8, tzinfo=time_zone))
    application.job_queue.run_daily(send_horoscope, time=time(8, 30, tzinfo=time_zone))


async def update_recipes_table(application: Application) -> None:
    count = await RecipiesRepo.count_recipes()
    if count == 0:
        recipes = parse_recipes(settings.recipes_path)
        await RecipiesRepo.add_recipes(recipes)


def main() -> None:
    """Start the bot."""
    logger.info("start bot")

    application = Application.builder().token(settings.token).post_init(update_recipes_table).build()

    add_handlers(application)
    add_jobs(application, settings.timezone)
    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
