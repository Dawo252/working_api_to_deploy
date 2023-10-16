import os
from pydantic_settings import BaseSettings
# from dotenv import load_dotenv


class Settings(BaseSettings):

    APP_NAME: str = "Cambling_app"
    APP_VERSION: str = "0.0.1"
    DEBUG: bool = os.getenv("DEBUG", False)


def get_settings():
    return Settings()
