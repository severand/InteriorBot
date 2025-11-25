import os
from dotenv import load_dotenv
import replicate

load_dotenv()
api_token = os.getenv("REPLICATE_API_TOKEN")

print(f"✓ Token loaded: {api_token[:20]}...")

try:
    print("✓ Testing with text-to-image model...")

    # Используем бесплатную модель для генерации изображений
    output = replicate.run(
        "stability-ai/sdxl",
        input={
            "prompt": "A modern cozy living room with minimalist interior design",
            "negative_prompt": "ugly, distorted",
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
    )

    print("✓ Generation successful!")
    print(f"✓ Image URL: {output}")

except Exception as e:
    print(f"✗ Error with SDXL: {e}")
    print("\nTrying alternative model...")

    try:
        # Резервный вариант
        output = replicate.run(
            "cjwbw/anything-v3.0",
            input={
                "prompt": "A modern living room",
            }
        )
        print("✓ Alternative model worked!")
        print(f"✓ Image URL: {output}")
    except Exception as e2:
        print(f"✗ Both models failed: {e2}")
