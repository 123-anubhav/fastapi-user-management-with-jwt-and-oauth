from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "User Management API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "mysql+pymysql://app_user:change_me@localhost:3306/user_management"
    jwt_secret_key: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    password_reset_expire_minutes: int = 15
    google_client_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    frontend_reset_url: str = "http://localhost:3000/reset-password"
    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_admin_password: str = "ChangeThisAdminPassword123!"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
