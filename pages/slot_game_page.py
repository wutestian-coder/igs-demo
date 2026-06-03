import time
import pathlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from config.settings import (
    GAME_HTML_PATH, SELENIUM_TIMEOUT,
    REEL_STOP_THRESHOLD, REEL_STOP_INTERVAL,
)
from utils.image_utils import png_bytes_to_array, is_motion_stopped


class SlotGamePage:

    _SPIN_BTN        = (By.ID, "spin-btn")
    _DATA_BAL        = (By.ID, "data-balance")
    _DATA_WIN        = (By.ID, "data-last-win")
    _DATA_BET        = (By.ID, "data-last-bet")
    _REELS_CONTAINER = (By.CLASS_NAME, "reels")

    def __init__(self, headless: bool = False):
        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=opts)
        self.wait   = WebDriverWait(self.driver, SELENIUM_TIMEOUT)

    def open(self):
        self.driver.get(pathlib.Path(GAME_HTML_PATH).as_uri())
        self.wait.until(EC.element_to_be_clickable(self._SPIN_BTN))

    def switch_bet(self, amount: int):
        self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f'.bet-btn[data-bet="{amount}"]')
        )).click()
        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, f'.bet-btn.active[data-bet="{amount}"]')
        ))

    def _read_hidden(self, locator: tuple) -> str:
        # display:none 的元素 .text 回傳空字串，需用 textContent
        el = self.wait.until(EC.presence_of_element_located(locator))
        return el.get_attribute("textContent")

    def read_balance(self) -> int:
        return int(self._read_hidden(self._DATA_BAL))

    def click_spin(self):
        self.wait.until(EC.element_to_be_clickable(self._SPIN_BTN)).click()

    def capture_reel_area(self) -> "np.ndarray":
        el = self.wait.until(EC.presence_of_element_located(self._REELS_CONTAINER))
        return png_bytes_to_array(el.screenshot_as_png)

    def wait_for_reel_stop_visual(self) -> None:
        """Confirm reel stop via OpenCV pixel-diff: requires 2 consecutive stable frames."""
        deadline = time.monotonic() + SELENIUM_TIMEOUT
        stable   = 0
        prev     = self.capture_reel_area()
        while time.monotonic() < deadline:
            time.sleep(REEL_STOP_INTERVAL)
            curr = self.capture_reel_area()
            if is_motion_stopped(prev, curr, REEL_STOP_THRESHOLD):
                stable += 1
                if stable >= 2:
                    return
            else:
                stable = 0
            prev = curr
        raise TimeoutError(f"轉軸未在 {SELENIUM_TIMEOUT}s 內停止（影像辨識）")

    def wait_for_spin_complete(self):
        self.wait.until(EC.element_to_be_clickable(self._SPIN_BTN))

    def read_win(self) -> int:
        return int(float(self._read_hidden(self._DATA_WIN)))

    def read_current_bet(self) -> int:
        return int(self._read_hidden(self._DATA_BET))

    def close(self):
        self.driver.quit()
