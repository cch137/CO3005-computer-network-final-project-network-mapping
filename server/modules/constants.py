import os
from dotenv import load_dotenv

load_dotenv(override=True)

IS_PRODUCTION_ENV = os.getenv("APP_ENV", "production").upper() in ("PROD", "PRODUCTION")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PORT = int(os.getenv("PORT", "6500" if IS_PRODUCTION_ENV else "6501"))

PARAPHRASE_MINILM_MAX_TOKENS = 128
