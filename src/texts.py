import json

with open("../phrases/supportive.json") as f:
    SUPPORTIVE_PHRASES = json.load(f)

MENU_TEXT = """Альманах рецептов подвала:
- [Таблица](https://docs.google.com/spreadsheets/d/1RWEh_VfmwvQC7PUXSIAjYruSO-cVYerEMvCcNu0H2EM/edit?usp=drivesdk)
- [Канал](https://t.me/+JemdAcrclhIzODcy)
"""

HELP_TEXT = """Доступные команды:
/menu название - отправить меню в канал
/show_menu - показать ссылку на меню
/ping - пинг бота
"""

JOIN_MESSAGE = """
Добро пожаловать в чат, {}! Заполни, пожалуйста, [анкету](https://docs.google.com/spreadsheets/d/12RuhcpwpdIgIfKq5pVkbMcqRe3b6MAt8OtedMURg2Sg/edit#gid=0)
"""

HOROSCOPE_PROMPT = "Сгенерируй абсурдный гороскоп на сегодня"
