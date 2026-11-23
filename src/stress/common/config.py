import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)  # Load environment variables from .env file

# Upstox API credentials (loaded from .env)
UPSTOX_API_KEY: str = os.getenv("UPSTOX_API_KEY", "")
UPSTOX_API_SECRET: str = os.getenv("UPSTOX_API_SECRET", "")
REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://127.0.0.1:8000/callback")

# Medallion architecture local data paths
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "data"))
BRONZE_DIR: Path = DATA_DIR / "bronze"
SILVER_DIR: Path = DATA_DIR / "silver"
GOLD_DIR: Path = DATA_DIR / "gold"

AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
# AZURE_CONTAINER_NAME: str = os.getenv("AZURE_CONTAINER_NAME", "HI EVERYONE")
AZURE_CONTAINER_NAME: str = os.getenv("AZURE_CONTAINER_NAME", "market-stress")