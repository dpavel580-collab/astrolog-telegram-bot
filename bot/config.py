import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID", "").strip()
OWNER_TG_LINK = os.getenv("OWNER_TG_LINK", "").strip()
MONO_PAYMENT_URL = os.getenv("MONO_PAYMENT_URL", "").strip()