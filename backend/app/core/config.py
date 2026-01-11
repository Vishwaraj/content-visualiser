from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # App Config
    PROJECT_NAME: str = "Concept Visualizer API"
    ENVIRONMENT: str = Field("development", description="dev, staging, or prod")
    LOG_LEVEL: str = Field("INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    
    # Concurrent Job Processing
    MAX_WORKERS: int = Field(4, description="Maximum number of concurrent background workers for job processing")

    # Security
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Gemini Config
    GEMINI_API_KEY: str = Field(..., description="Get this from aistudio.google.com")
    GEMINI_MODEL: str = "gemini-2.5-flash" # Updated model for potentially better performance or features

    # Loads .env file if present
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings() 