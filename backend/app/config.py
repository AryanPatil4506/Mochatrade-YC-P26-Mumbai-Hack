import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.ALLOW_THRESHOLD: int = int(os.getenv("ALLOW_THRESHOLD", "60"))
        self.APPROVAL_THRESHOLD: int = int(os.getenv("APPROVAL_THRESHOLD", "80"))
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")
        self.RISK_PROVIDER: str = os.getenv("RISK_PROVIDER", "mock")
        self.BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8008"))
        self.FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "5175"))

settings = Settings()
