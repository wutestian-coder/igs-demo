import pathlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from config.settings import GAME_HTML_PATH, SELENIUM_TIMEOUT


class SlotGamePage:

    _SPIN_BTN  = (By.ID, "spin-btn")
    _DATA_BAL  = (By.ID, "data-balance")
    _DATA_WIN  = (By.ID, "data-last-win")
    _DATA_BET  = (By.ID, "data-last-bet")

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
        # display:none 的元素 .text 會回傳空字串，需用 textContent
        el = self.wait.until(EC.presence_of_element_located(locator))
        return el.get_attribute("textContent")

    def read_balance(self) -> int:
        return int(self._read_hidden(self._DATA_BAL))

    def click_spin(self):
        self.wait.until(EC.element_to_be_clickable(self._SPIN_BTN)).click()

    def wait_for_spin_complete(self):
        self.wait.until(EC.element_to_be_clickable(self._SPIN_BTN))

    def read_win(self) -> int:
        return int(float(self._read_hidden(self._DATA_WIN)))

    def read_current_bet(self) -> int:
        return int(self._read_hidden(self._DATA_BET))

    def close(self):
        self.driver.quit()
