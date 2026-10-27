from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Washing Machine CMS."""

    app_name: str = "Washing Machine Complaint Management System"
    app_version: str = "1.0.0"
    debug: bool = True

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "washing_machine_cms"
    db_user: str = "cms_app"
    db_password: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()