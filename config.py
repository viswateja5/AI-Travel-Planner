import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = (PROJECT_ROOT / ".env").resolve()


def load_project_env() -> Path:
    """Load the backend project-root .env file without depending on the terminal working directory."""
    load_dotenv(dotenv_path=str(ENV_PATH), override=True)
    return ENV_PATH


load_project_env()

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DATABASE_DIR = PROJECT_ROOT / "database"

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
GEMINI_MODEL = (os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite").strip() or "gemini-3.5-flash-lite"
GEMINI_TIMEOUT_SECONDS = int((os.getenv("GEMINI_TIMEOUT_SECONDS") or "90").strip() or "90")

DEFAULT_BUDGET_MODE = os.getenv("DEFAULT_BUDGET_MODE", "standard")
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "INR").upper()
ENABLE_TRIP_HISTORY = os.getenv("ENABLE_TRIP_HISTORY", "true").lower() in {"1", "true", "yes"}

OUTPUT_MD_PATH = OUTPUTS_DIR / "travel_plan.md"
OUTPUT_PDF_PATH = OUTPUTS_DIR / "travel_plan.pdf"
DB_PATH = DATABASE_DIR / "travel_history.db"


def get_gemini_diagnostic() -> dict[str, object]:
    """Return a safe readiness check without exposing the key's value."""
    return {
        "gemini_api_key_configured": bool(GEMINI_API_KEY),
        "gemini_model": GEMINI_MODEL,
        "env_file": str(ENV_PATH),
    }
