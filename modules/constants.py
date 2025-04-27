import os
from dotenv import load_dotenv

load_dotenv(override=True)

IS_PRODUCTION_ENV = os.getenv("APP_ENV", "production").upper() in ("PROD", "PRODUCTION")
PORT = int(os.getenv("PORT", "6500" if IS_PRODUCTION_ENV else "6501"))

PARAPHRASE_MINILM_MAX_TOKENS = 128
