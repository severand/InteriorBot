import os
import logging
import requests
import aiohttp
from aiogram import Bot
from config import config

logger = logging.getLogger(__name__)

# ID модели Replicate для генерации интерьеров
MODEL_ID = "adirik/interior-design:76604baddc85b1b4616e1c6475eca080da339c8875bd4996705440484a6879c2"

# URL Colab API (потом заменишь на реальный)
COLAB_API_URL = os.getenv("COLAB_API_URL", "http://localhost:5000")

# Маппинг стилей на промпты
STYLE_PROMPTS = {
    'modern': 'modern contemporary interior design, clean lines, neutral colors, sleek furniture, minimalist aesthetic',
    'minimalist': 'minimalist interior design, simple forms, functional space, clean aesthetic, uncluttered, neutral palette',
    'scandinavian': 'Scandinavian interior design, light wood, white walls, natural lighting, cozy hygge atmosphere, functional beauty',
    'industrial': 'industrial loft interior design, exposed brick, metal fixtures, concrete floors, open space, raw materials',
    'rustic': 'rustic country interior design, natural materials, warm wood tones, stone accents, cozy cottage feel',
    'japandi': 'Japandi interior design, Japanese minimalism meets Scandinavian, natural wood, clean lines, zen atmosphere, wabi-sabi aesthetic',
    'boho': 'bohemian eclectic interior design, colorful textiles, layered patterns, plants, vintage pieces, relaxed vibe',
    'mediterranean': 'Mediterranean interior design, terracotta, blue and white colors, natural textures, arched doorways, sunny atmosphere',
    'midcentury': 'mid-century modern vintage interior design, retro furniture, organic shapes, wood and leather, 1950s-60s aesthetic',
    'artdeco': 'Art Deco interior design, geometric patterns, luxurious materials, bold colors, glamorous 1920s-30s style, metallic accents',
}

# Маппинг комнат
ROOM_PROMPTS = {
    'living_room': 'living room',
    'bedroom': 'bedroom',
    'kitchen': 'kitchen',
    'bathroom': 'bathroom',
    'office': 'home office',
    'dining_room': 'dining room',
}


def get_prompt(style: str, room: str) -> str:
    """Генерирует промпт на основе стиля и комнаты."""
    style_desc = STYLE_PROMPTS.get(style, 'modern interior design')
    room_name = ROOM_PROMPTS.get(room, room.replace('_', ' '))
    prompt = f"A beautiful {room_name}, {style_desc}, photorealistic, 8k, high quality, professional photography"
    return prompt


async def generate_image_via_colab(prompt: str) -> str | None:
    """
    Генерирует изображение через Colab API.

    Args:
        prompt: Текстовый промпт для генерации

    Returns:
        URL сгенерированного изображения или None
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{COLAB_API_URL}/generate",
                    json={"prompt": prompt},
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 минут таймаут
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('image_url')
                else:
                    logger.error(f"Colab API error: {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка при генерации через Colab: {e}")
        return None


async def generate_image_via_replicate(photo_file_id: str, room: str, style: str, bot_token: str) -> str | None:
    """
    Генерирует изображение через Replicate API (старый способ).
    Используется если Colab недоступен.
    """

    if not config.REPLICATE_API_TOKEN or config.REPLICATE_API_TOKEN == "FAKE_TOKEN_FOR_TEST":
        logger.warning("REPLICATE_API_TOKEN не установлен")
        return None

    try:
        import replicate
        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        prompt = get_prompt(style, room)
        logger.info(f"Генерация через Replicate: {prompt}")

        bot = Bot(token=bot_token)
        file_info = await bot.get_file(photo_file_id)
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}"

        output = replicate.run(
            MODEL_ID,
            input={
                "image": file_url,
                "prompt": prompt,
                "room_type": room.replace('_', ' '),
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
            }
        )

        if output:
            if isinstance(output, str):
                return output
            elif isinstance(output, list) and len(output) > 0:
                return output[0]

    except Exception as e:
        logger.error(f"Ошибка при генерации через Replicate: {e}")

    return None


async def generate_image(photo_file_id: str, room: str, style: str, bot_token: str) -> str | None:
    """
    Главная функция генерации. Пробует:
    1. Colab API (основной способ)
    2. Replicate API (резервный способ)
    """

    prompt = get_prompt(style, room)

    # Сначала пробуем Colab
    logger.info(f"Попытка 1: Генерация через Colab API...")
    result = await generate_image_via_colab(prompt)

    if result:
        logger.info(f"✅ Генерация через Colab успешна")
        return result

    # Если Colab не сработал, пробуем Replicate
    logger.info(f"Попытка 2: Генерация через Replicate API...")
    result = await generate_image_via_replicate(photo_file_id, room, style, bot_token)

    if result:
        logger.info(f"✅ Генерация через Replicate успешна")
        return result

    logger.error("❌ Обе попытки генерации не удались")
    return None
