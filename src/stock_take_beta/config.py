from pathlib import Path

APP_NAME = "Stock Take Beta"
APP_SUBTITLE = "Massimo's Rail · Shorts stock audit"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DATA_DIR = PROJECT_ROOT / "data"
PROGRESS_FILE = LOCAL_DATA_DIR / "stock_take_progress.json"
CROSSLIST_PROFILE_DIR = LOCAL_DATA_DIR / "crosslist_chrome_profile"
MOBILE_HOST = "0.0.0.0"
MOBILE_PORT = 5055

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
