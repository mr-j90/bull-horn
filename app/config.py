from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LinkedIn
    linkedin_access_token: str = ""

    # X / Twitter
    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_secret: str = ""

    # App
    posts_file: str = "posts/queue.json"
    scheduler_cron: str = "0 * * * *"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
