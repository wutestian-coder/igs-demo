import os

PROJECT_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_HTML_PATH  = os.path.join(PROJECT_ROOT, "slot_game.html")
REPORTS_DIR     = os.path.join(PROJECT_ROOT, "reports")
SELENIUM_TIMEOUT = 10  # seconds

# OpenCV reel-stop detection
REEL_STOP_THRESHOLD = 1.0   # mean pixel diff (0–255); below this → stable frame
REEL_STOP_INTERVAL  = 0.15  # seconds between sampled frames
