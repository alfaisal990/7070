from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Self

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/taskdb"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @model_validator(mode="after")
    def validate_secret_key(self) -> Self:
        insecure_keys = ["supersecretkeychangeinproduction", "yoursecretkeyherechangeinproduction123"]
        if not hasattr(self, "SECRET_KEY") or not self.SECRET_KEY or self.SECRET_KEY.strip() == "" or self.SECRET_KEY in insecure_keys:
            raise ValueError("SECRET_KEY must be a secure, non-default value in production.")
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
