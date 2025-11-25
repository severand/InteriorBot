import os
from dotenv import load_dotenv
import replicate

load_dotenv()

print("Testing image-to-image models...")

# Тестируем реально image-to-image модели
models_to_try = [
    ("stability-ai/sdxl", "sdxl with image"),
    ("stable-diffusion-v1-5", "sd1.5 with image"),
]

test_prompt = "modern minimalist living room, clean lines, neutral colors"
test_image_url = "https://i.imgur.com/K1x5d1H.png"  # Любое тестовое изображение

for model_name, desc in models_to_try:
    try:
        print(f"\n✓ Testing {desc}...")
        output = replicate.run(
            model_name,
            input={
                "image": test_image_url,
                "prompt": test_prompt,
                "strength": 0.7,
            }
        )
        print(f"✓✓✓ SUCCESS: {desc}!")
        print(f"Output: {output}")
        break
    except Exception as e:
        print(f"✗ {desc}: {str(e)[:150]}")
