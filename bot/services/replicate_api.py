import os
import logging
from aiogram import Bot
from config import config

logger = logging.getLogger(__name__)

# ID модели Replicate для генерации интерьеров
MODEL_ID = "adirik/interior-design:76604baddc85b1b4616e1c6475eca080da339c8875bd4996705440484a6879c2"

# Маппинг стилей на промпты (обновлено с новыми стилями)
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


async def generate_image(photo_file_id: str, room: str, style: str, bot_token: str) -> str | None:
    """
    Вызывает API Replicate для генерации изображения интерьера.

    Args:
        photo_file_id: ID фото из Telegram
        room: Тип комнаты (living_room, bedroom, kitchen и т.д.)
        style: Стиль дизайна (modern, minimalist, scandinavian и т.д.)
        bot_token: Токен бота для загрузки фото

    Returns:
        URL сгенерированного изображения или None при ошибке
    """

    # Проверяем наличие API токена
    if not config.REPLICATE_API_TOKEN or config.REPLICATE_API_TOKEN == "FAKE_TOKEN_FOR_TEST":
        logger.warning("REPLICATE_API_TOKEN не установлен, используется заглушка")
        return "https://i.imgur.com/K1x5d1H.png"

    try:
        # Импортируем replicate только если токен есть
        import replicate

        # Устанавливаем токен для клиента
        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        # Генерируем промпт
        prompt = get_prompt(style, room)
        logger.info(f"Генерация изображения с промптом: {prompt}")

        # Получаем URL файла из Telegram
        bot = Bot(token=bot_token)
        file_info = await bot.get_file(photo_file_id)
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}"
        logger.info(f"URL исходного изображения: {file_url}")

        # Вызываем Replicate API
        logger.info("Отправка запроса в Replicate API...")
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

        # Обрабатываем результат
        if output:
            # output может быть строкой (URL) или списком URL
            if isinstance(output, str):
                logger.info(f"Генерация успешна: {output}")
                return output
            elif isinstance(output, list) and len(output) > 0:
                result_url = output[0]
                logger.info(f"Генерация успешна: {result_url}")
                return result_url
            else:
                logger.error(f"Неожиданный формат ответа: {output}")
                return None

        logger.error("API вернул пустой результат")
        return None

    except ImportError:
        logger.error("Библиотека replicate не установлена. Выполните: pip install replicate")
        return None
    except Exception as e:
        logger.error(f"Ошибка при генерации через Replicate API: {e}", exc_info=True)
        return None