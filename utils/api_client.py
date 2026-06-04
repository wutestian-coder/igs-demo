import json
import random as _random


class SlotApiClient:
    """WebSocket client for live game server API testing."""

    def __init__(self, ws_url: str):
        import websocket
        self._ws  = websocket.WebSocket()
        self._url = ws_url

    def connect(self) -> dict:
        """Connect and return initial state: {"balance": int, ...}"""
        self._ws.connect(self._url)
        return json.loads(self._ws.recv())

    def spin(self, bet: int) -> dict:
        """Send spin request and return: {"reels": list, "win": int, "balance": int}"""
        self._ws.send(json.dumps({"action": "spin", "bet": bet}))
        return json.loads(self._ws.recv())

    def close(self):
        self._ws.close()


class MockSlotApiClient:
    """Offline mock — same game logic and intentional bug as MockSlotPage."""

    _SYMBOLS  = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
    _PAYTABLE = {
        ("💎","💎","💎"): 50, ("7️⃣","7️⃣","7️⃣"): 30, ("⭐","⭐","⭐"): 20,
        ("🍊","🍊","🍊"): 10, ("🍋","🍋","🍋"): 8,  ("🍒","🍒","🍒"): 5,
    }

    def __init__(self):
        self._balance    = 1000
        self._spin_count = 0

    def connect(self) -> dict:
        return {"balance": self._balance}

    def spin(self, bet: int) -> dict:
        if self._balance < bet:
            raise RuntimeError("餘額不足")
        self._balance    -= bet
        self._spin_count += 1

        reels      = [_random.choice(self._SYMBOLS) for _ in range(3)]
        multiplier = self._PAYTABLE.get(tuple(reels), 0)
        if multiplier == 0 and reels[0] == "🍒" and reels[1] == "🍒":
            multiplier = 2
        win = multiplier * bet // 10

        # Bug: 第 7 次有贏分時只入帳一半，模擬金流計算 Bug
        actual        = win // 2 if self._spin_count == 7 and win > 0 else win
        self._balance += actual

        return {"reels": reels, "win": win, "balance": self._balance}

    def close(self):
        pass
