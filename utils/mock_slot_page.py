import random


class MockSlotPage:

    _SYMBOLS  = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
    _PAYTABLE = {
        ("💎","💎","💎"): 50, ("7️⃣","7️⃣","7️⃣"): 30, ("⭐","⭐","⭐"): 20,
        ("🍊","🍊","🍊"): 10, ("🍋","🍋","🍋"): 8,  ("🍒","🍒","🍒"): 5,
    }

    def __init__(self):
        self._balance     = 1000
        self._current_bet = 10
        self._last_win    = 0
        self._pending_win = 0
        self._spin_count  = 0

    def open(self): pass

    def switch_bet(self, amount: int):
        self._current_bet = amount

    def read_balance(self) -> int:
        return self._balance

    def click_spin(self):
        if self._balance < self._current_bet:
            raise RuntimeError("餘額不足，無法下注")
        self._balance -= self._current_bet

        reels = [random.choice(self._SYMBOLS) for _ in range(3)]
        win   = self._PAYTABLE.get(tuple(reels), 0)
        if win == 0 and reels[0] == "🍒" and reels[1] == "🍒":
            win = 2
        self._pending_win = win * self._current_bet // 10
        self._spin_count += 1

    def wait_for_spin_complete(self):
        win = self._pending_win
        # 第 7 次有贏分時只入帳一半，模擬金流計算 Bug
        actual        = win // 2 if self._spin_count == 7 and win > 0 else win
        self._balance += actual
        self._last_win = win

    def wait_for_reel_stop_visual(self):
        self.wait_for_spin_complete()

    def read_win(self) -> int:
        return self._last_win

    def read_current_bet(self) -> int:
        return self._current_bet

    def close(self): pass
