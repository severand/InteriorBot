import os
from dotenv import load_dotenv
import replicate

load_dotenv()

print("Testing API token...")
try:
    # Простой тест доступности
    result = replicate.run(
        "replicate/hello-world",
        input={}
    )
    print("✓ API работает!")
    print(f"✓ Result: {result}")
except Exception as e:
    print(f"✗ Error: {e}")
