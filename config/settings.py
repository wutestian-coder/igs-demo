import os

PROJECT_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_HTML_PATH  = os.path.join(PROJECT_ROOT, "slot_game.html")
REPORTS_DIR     = os.path.join(PROJECT_ROOT, "reports")
SELENIUM_TIMEOUT = 10  # seconds
