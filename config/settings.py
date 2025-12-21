# config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path
import os

# Load .env from project root
ENV_PATH = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):
    """Application settings with validation"""

    # MongoDB
    mongodb_uri_local: str = Field("mongodb://localhost:27017", env="MONGODB_URI_LOCAL")
    mongodb_uri_docker: str = Field("mongodb://host.docker.internal:27017", env="MONGODB_URI_DOCKER")
    mongodb_uri: str = Field("mongodb://localhost:27017", description="Selected MongoDB URI at runtime")  # ✅ default provided
    db_name: str = Field("face_attendance", env="DB_NAME")

    # Recognition
    similarity_threshold: float = Field(0.62, env="SIMILARITY_THRESHOLD")
    min_photos: int = Field(3, env="MIN_PHOTOS")

    # Liveness
    liveness_required: bool = Field(False, env="LIVENESS_REQUIRED")

    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Model paths
    retinaface_model: str = "models/retinaface.onnx"
    arcface_model: str = "models/arcface_r100_glint360k.onnx"

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set mongodb_uri dynamically based on environment
        if os.environ.get("RUNNING_IN_DOCKER", "0") == "1":
            object.__setattr__(self, "mongodb_uri", self.mongodb_uri_docker)
        else:
            object.__setattr__(self, "mongodb_uri", self.mongodb_uri_local)

# Instantiate settings
settings = Settings()

# Optional: print confirmation
from rich.console import Console
console = Console()
console.print(f"[green]MongoDB URI selected:[/green] {settings.mongodb_uri}")
