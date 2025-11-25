import os
from dotenv import load_dotenv
import replicate

load_dotenv()

print("Testing basic Replicate connection...")

# Попробуем самую базовую модель
models_to_try = [
    "stability-ai/sdxl",
    "stability-ai/stable-diffusion-3",
    "black-forest-labs/flux-pro",
    "replicate/hello-world",  # Тестовая модель
]

for model in models_to_try:
    try:
        print(f"\n✓ Trying {model}...")
        if model == "replicate/hello-world":
            output = replicate.run(model, input={})
        else:
            output = replicate.run(
                model,
                input={"prompt": "test"}
            )
        print(f"✓✓✓ SUCCESS with {model}!")
        print(f"Output: {output}")
        break
    except Exception as e:
        print(f"✗ {model}: {str(e)[:100]}")
