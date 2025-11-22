import os
from dotenv import load_dotenv

load_dotenv()

# --- АДМИНИСТРАТОРЫ ---
ADMIN_IDS = [
    7884972750,
    827652042,
    5426993389,
    6999935990
]

class Config:
    """Configuration class for bot settings"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
    YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
    YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')

    # Database settings
    DB_PATH = 'bot.db'

    # Free generations for new users
    FREE_GENERATIONS = 3

    PAYMENT_PACKAGES = {
        'small': {'tokens': 10, 'price': 290, 'name': '10 генераций'},
        'medium': {'tokens': 25, 'price': 590, 'name': '25 генераций'},
        'large': {'tokens': 60, 'price': 990, 'name': '60 генераций'},
    }

config = Config()