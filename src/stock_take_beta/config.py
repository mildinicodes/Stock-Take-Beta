from pathlib import Path

APP_NAME = "Stock Take Beta"
APP_SUBTITLE = "Massimo's Rail · Shorts stock audit"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DATA_DIR = PROJECT_ROOT / "data"
PROGRESS_FILE = LOCAL_DATA_DIR / "stock_take_progress.json"

COLORS = {
    "cream": "#F3EBDD",
    "cream_light": "#FBF7EF",
    "green": "#173C2B",
    "green_mid": "#285440",
    "green_soft": "#DCE6DE",
    "text": "#173C2B",
    "muted": "#6E776F",
    "border": "#CFC6B7",
    "white": "#FFFFFF",
}
