import os
from dotenv import load_dotenv

load_dotenv(override=True)

IS_PRODUCTION_ENV = os.getenv("APP_ENV", "production").upper() in ("PROD", "PRODUCTION")

PARAPHRASE_MINILM_MAX_TOKENS = 128
