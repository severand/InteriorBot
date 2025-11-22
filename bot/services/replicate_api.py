import os
import replicate
import requests
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

# Используем фейковый токен для теста, если реальный не указан
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "FAKE_TOKEN_FOR_TEST")

# ID модели Replicate
MODEL_ID = "jag-design/interior-design:a232f38d17a78361738734e5695029e246944e27f066b1d1fdd2c9f5928d132c"


def get_prompt(style: str, room: str) -> str:
    """Генерирует промпт на основе стиля и комнаты."""
    prompt_template = f"a luxurious {room}, interior design, {style} style, natural lighting, high quality photo, 8k, photorealistic"
    return prompt_template.encode('utf-8', errors='ignore').decode('utf-8')


async def generate_image(photo_file_id: str, room: str, style: str, bot_token: str) -> str | None:
    """
    Вызывает API Replicate для генерации изображения.
    (Принимает bot_token для загрузки файла из Telegram)
    """

    if REPLICATE_API_TOKEN == "FAKE_TOKEN_FOR_TEST":
        print("--- ИСПОЛЬЗУЕТСЯ ФЕЙКОВАЯ ГЕНЕРАЦИЯ ---")
        return "https://i.imgur.com/K1x5d1H.png"  # Исправленная рабочая заглушка

    # --- НАЧАЛО РЕАЛЬНОЙ ЛОГИКИ API ---
    try:
        prompt = get_prompt(style, room)

        # 1. Получаем URL файла из Telegram, используя Bot(token)
        bot = Bot(token=bot_token)
        file_info = await bot.get_file(photo_file_id)
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}"

        # 2. Вызываем Replicate API
        output = replicate.run(
            MODEL_ID,
            input={
                "image": file_url,
                "prompt": prompt,
                "target_room": room.replace('_', ' '),
                "target_style": style,
                "structure_weight": 0.5,
                "guidance_scale": 7.5,
            }
        )

        if output and isinstance(output, list) and len(output) > 0:
            print(f"--- ГЕНЕРАЦИЯ УСПЕШНА ---")
            return output[0]

        return None

    except Exception as e:
        print(f"--- ОШИБКА REPLICATE API: {e} ---")
        return None