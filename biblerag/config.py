from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BIBLE_PATH = DATA_DIR / "bible" / "en_kjv.json"
PEOPLE_PATH = DATA_DIR / "people.json"
INDEX_DIR = DATA_DIR / "index"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o-mini"
    biblerag_api_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    collection_name: str = "bible_rag"


settings = Settings()
