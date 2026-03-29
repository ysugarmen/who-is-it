from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    cors_origins: str = "http://localhost:5173"
    fuzzy_match_threshold: int = 85

    model_config = {"env_file": ".env"}

settings = Settings()
