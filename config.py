import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    PORTAL_LOGIN_URL: str = Field(
        default=os.getenv("PORTAL_LOGIN_URL", "http://13.228.179.22/examsignin.php?session=true")
    )
    DEFAULT_STUDENT_ID: str = Field(
        default=os.getenv("STUDENT_ID", "SRU202300876314")
    )
    HEADLESS: bool = Field(
        default=os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    )
    SLOW_MO_MS: int = Field(default=int(os.getenv("SLOW_MO_MS", "50")))
    USER_DATA_DIR: str = Field(
        default=os.getenv("USER_DATA_DIR", os.path.join(os.path.dirname(__file__), ".browser_profile"))
    )
    DASHBOARD_PORT: int = Field(default=int(os.getenv("DASHBOARD_PORT", "8000")))
    STRICT_HUMAN_CONTROL: bool = True  # Hard safety rule: Never auto-submit

settings = Settings()
