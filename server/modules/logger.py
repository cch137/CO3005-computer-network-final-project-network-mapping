import logging
from .constants import IS_PRODUCTION_ENV

# 建立 logger
logger = logging.getLogger(__name__)

# 設定日誌格式
formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")

# 建立 console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 根據環境設定 log level
if IS_PRODUCTION_ENV:
    logger.setLevel(logging.WARNING)
    console_handler.setLevel(logging.WARNING)
else:
    logger.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

logger.addHandler(console_handler)
