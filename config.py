import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

ADMIN_IDS = [7025174146]  # ← ТВОЙ ID

PREMIUM_PRICE_STARS = 1
PREMIUM_DAYS = 30