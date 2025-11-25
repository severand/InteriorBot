import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("REPLICATE_API_TOKEN")

print(f"Token from .env: {token}")
print(f"Token starts with: {token[:10] if token else 'NOT FOUND'}")
print(f"Token length: {len(token) if token else 0}")
