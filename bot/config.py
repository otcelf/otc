from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    bot_username: str
    support_username: str
    owner_id: int
    start_image_url: str
    banner_path: str
    db_path: str
    proxy_url: str = ""


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required in .env")

    return Settings(
        bot_token=bot_token,
        bot_username=os.getenv("BOT_USERNAME", "StellarGarantBot").strip(),
        support_username=os.getenv("SUPPORT_USERNAME", "StellarOTCSupport").strip(),
        owner_id=int(os.getenv("OWNER_ID", "6930148555").strip()),
        start_image_url=os.getenv("START_IMAGE_URL", "").strip(),
        banner_path=os.getenv("BANNER_PATH", "banner.jpg").strip(),
        db_path=os.getenv("DB_PATH", "bot.db").strip(),
        proxy_url=os.getenv("PROXY_URL", "").strip(),
    )
