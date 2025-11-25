# https://www.perplexity.ai/search/izuchi-moi-kod-na-git-khab-i-p-iLN8v2F.Rkqx2s4l9WxSOw#102


import os
import logging
from aiogram import Bot
from config import config

logger = logging.getLogger(__name__)

MODEL_ID = "black-forest-labs/flux-1.1-pro"

STYLE_PROMPTS = {
    'modern': 'modern minimalist interior design, clean lines, neutral colors, professional photography, 4K',
    'minimalist': 'minimalist interior, simple forms, functional space, uncluttered, zen, professional, 4K',
    'scandinavian': 'Scandinavian interior, light wood, white walls, natural lighting, cozy, professional, 4K',
    'industrial': 'industrial loft, exposed brick, metal fixtures, concrete, open space, professional, 4K',
    'rustic': 'rustic cozy interior, natural wood, warm tones, stone, cottage, professional, 4K',
    'japandi': 'Japandi interior, Japanese minimalism, Scandinavian, wood, zen, professional, 4K',
    'boho': 'bohemian interior, colorful, layered patterns, plants, vintage, professional, 4K',
    'mediterranean': 'Mediterranean interior, terracotta, blue white, natural, professional, 4K',
    'midcentury': 'mid-century modern interior, retro, organic shapes, wood, professional, 4K',
    'artdeco': 'Art Deco interior, geometric, luxurious, bold colors, glamorous, professional, 4K',
}

ROOM_PROMPTS = {
    'living_room': 'living room',
    'bedroom': 'bedroom',
    'kitchen': 'kitchen',
    'bathroom': 'bathroom',
    'office': 'office',
    'dining_room': 'dining room',
}

def get_prompt(style: str, room: str) -> str:
    style_desc = STYLE_PROMPTS.get(style, 'modern')
    room_name = ROOM_PROMPTS.get(room, room.replace('_', ' '))
    return f"A beautiful {room_name} with {style_desc}, interior design magazine quality"

async def generate_image(photo_file_id: str, room: str, style: str, bot_token: str) -> str | None:
    if not config.REPLICATE_API_TOKEN:
        return "https://i.imgur.com/K1x5d1H.png"

    try:
        import replicate
        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        prompt = get_prompt(style, room)
        logger.info(f"🎨 FLUX PRO: {room} → {style}")

        output = replicate.run(
            MODEL_ID,
            input={
                "prompt": prompt,
                "steps": 25,
                "width": 1024,
                "height": 1024,
                "guidance": 3,
                "aspect_ratio": "1:1",
                "output_format": "webp",
                "output_quality": 85,
            }
        )

        if output:
            try:
                return output.url()
            except:
                return str(output)
        return None

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return None
