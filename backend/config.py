from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    cc_key: str = ""
    cc_base_url: str = "https://api.cloudcruise.com"
    cc_dry_run: bool = True
    database_url: str = "sqlite:///./poc_cloudcruise.db"


settings = Settings()
