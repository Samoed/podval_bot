from openai import OpenAI
from settings import Settings
from texts import HOROSCOPE_PROMPT


class LLM:
    settings = Settings()
    client = OpenAI(api_key=settings.openai_api_key)

    @classmethod
    def get_response(cls, prompt: str) -> str:
        response = cls.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4o-mini",
        )
        return response.choices[0].message.content if response.choices[0].message.content is not None else ""

    @classmethod
    def generate_horoscope(cls, prompt: str = HOROSCOPE_PROMPT) -> str:
        return cls.get_response(prompt)
