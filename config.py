import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
DATABASE_DIR = BASE_DIR / "database"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_BUDGET_MODE = os.getenv("DEFAULT_BUDGET_MODE", "standard")
ENABLE_TRIP_HISTORY = os.getenv("ENABLE_TRIP_HISTORY", "true").lower() in {"1", "true", "yes"}

OUTPUT_MD_PATH = OUTPUTS_DIR / "travel_plan.md"
OUTPUT_PDF_PATH = OUTPUTS_DIR / "travel_plan.pdf"
DB_PATH = DATABASE_DIR / "travel_history.db"
