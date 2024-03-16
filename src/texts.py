import json
import os

from settings import Settings

settings = Settings()
directory = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(directory, settings.supportive_phrases_path)) as f:
    SUPPORTIVE_PHRASES = json.load(f)

with open(os.path.join(directory, settings.user_supportive_phrases_path)) as f:
    USER_SUPPORTIVE = json.load(f)

print("Loaded phrases from json files", len(SUPPORTIVE_PHRASES), len(USER_SUPPORTIVE))

MENU_TEXT = """Альманах рецептов подвала:
- [Таблица](https://docs.google.com/spreadsheets/d/1RWEh_VfmwvQC7PUXSIAjYruSO-cVYerEMvCcNu0H2EM/edit?usp=drivesdk)
- [Канал](https://t.me/+JemdAcrclhIzODcy)
"""

HELP_TEXT = """Доступные команды:
/menu название (или /add_recipe) - отправить меню в канал
/show_menu - показать ссылку на меню
/search_recipe название - поиск рецепта по названию
/ping - пинг бота
"""

JOIN_MESSAGE = """
Добро пожаловать в чат, {}! Заполни, пожалуйста, [анкету](https://docs.google.com/spreadsheets/d/12RuhcpwpdIgIfKq5pVkbMcqRe3b6MAt8OtedMURg2Sg/edit#gid=0)

Также есть [чат в Instagram](https://ig.me/j/AbYRJGSfV-bp8nMa/), где кидаемся смешными рилсами
"""

HOROSCOPE_PROMPT = (
    "Сгенерируй абсурдный гороскоп на сегодня. Пиши текст сразу. Каждый знак зодиака должен быть в отдельной строчке."
)
