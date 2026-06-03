"""
品檢軟體工程師 初試題目
Slot 遊戲自動化測試 - 資深 QA 版本

測試策略：
1. 基本金流驗證（每次 spin 的資產變化正確性）
2. 累積金流驗證（10 次後總資產是否合理）
3. Edge Case：餘額不足保護
4. Edge Case：押注切換後是否正確生效
5. 異常偵測：贏分顯示 vs 實際入帳是否一致
"""

import time
import openpyxl
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


# ═══════════════════════════════════════════════════════════
#  測試資料結構
# ═══════════════════════════════════════════════════════════

class TestRecord:
    def __init__(self):
        self.index = 0
        self.test_time = ""
        self.balance_before = 0
        self.bet = 0
        self.win_displayed = 0      # 畫面顯示的贏分
        self.balance_after = 0
        self.expected_balance = 0   # 金流公式計算的預期值
        self.pass_fail = ""
        self.fail_reason = ""       # 資深 QA 核心：記錄具體失敗原因

    def validate(self):
        """
        金流驗證邏輯：
        資產(前) - 押注 + 贏分 == 資產(後)
        同時檢查多種異常情境
        """
        self.expected_balance = self.balance_before - self.bet + self.win_displayed
        reasons = []

        # 1. 基本金流驗證
        if self.balance_after != self.expected_balance:
            diff = self.balance_after - self.expected_balance
            reasons.append(f"金流異常(差{diff:+d})")

        # 2. 餘額不應該出現負數
        if self.balance_after < 0:
            reasons.append("餘額出現負值")

        # 3. 贏分不應該是負數
        if self.win_displayed < 0:
            reasons.append("贏分出現負值")

        # 4. 押注不應超過下注前餘額
        if self.bet > self.balance_before:
            reasons.append("押注超過餘額仍可下注")

        if reasons:
            self.pass_fail = "FAIL"
            self.fail_reason = " | ".join(reasons)
        else:
            self.pass_fail = "PASS"
            self.fail_reason = "-"

        return self.pass_fail == "PASS"


# ═══════════════════════════════════════════════════════════
#  Selenium 驅動（真實網頁自動化）
# ═══════════════════════════════════════════════════════════

class SlotGameDriver:
    """操作真實 Slot 網頁的自動化驅動"""

    def __init__(self, html_path: str):
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("請先安裝 selenium：pip install selenium")

        options = Options()
        options.add_argument("--headless")          # 背景執行（面試現場可拿掉看畫面）
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=options)
        self.driver.get(f"file://{html_path}")
        self.wait = WebDriverWait(self.driver, 10)

        # 等待頁面載入
        self.wait.until(EC.presence_of_element_located((By.ID, "spin-btn")))
        time.sleep(0.5)

    def switch_bet(self, amount: int):
        """步驟 1：切換 bet 到指定金額"""
        btn = self.driver.find_element(By.CSS_SELECTOR, f'[data-bet="{amount}"]')
        btn.click()
        time.sleep(0.2)

    def read_balance(self) -> int:
        """步驟 2 / 步驟 5：從隱藏欄位讀取當前資產（精確值）"""
        text = self.driver.find_element(By.ID, "data-balance").text
        return int(text)

    def spin(self):
        """步驟 3：點擊 spin 按鈕"""
        btn = self.driver.find_element(By.ID, "spin-btn")
        btn.click()

    def wait_for_stop(self):
        """步驟 4：確認停輪（等待 game-state 變成 done）"""
        self.wait.until(
            lambda d: d.find_element(By.ID, "data-game-state").text == "done"
        )
        time.sleep(0.1)

    def read_win(self) -> int:
        """步驟 5：讀取贏分（從隱藏欄位）"""
        text = self.driver.find_element(By.ID, "data-last-win").text
        return int(float(text))

    def read_bet(self) -> int:
        """讀取當前押注"""
        text = self.driver.find_element(By.ID, "data-last-bet").text
        return int(text)

    def close(self):
        self.driver.quit()


# ═══════════════════════════════════════════════════════════
#  模擬驅動（無 Selenium 環境時使用）
# ═══════════════════════════════════════════════════════════

class MockSlotGameDriver:
    """
    模擬真實網頁行為的驅動
    刻意注入 Bug（第 7 次贏分入帳只給一半），測試是否能被發現
    """
    import random as _random

    SYMBOLS = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
    PAYTABLE = {
        ("💎","💎","💎"): 50, ("7️⃣","7️⃣","7️⃣"): 30, ("⭐","⭐","⭐"): 20,
        ("🍊","🍊","🍊"): 10, ("🍋","🍋","🍋"): 8,  ("🍒","🍒","🍒"): 5,
    }

    def __init__(self):
        self._balance = 1000
        self._current_bet = 10
        self._last_win = 0
        self._spin_count = 0
        self._inject_bug = True  # 模擬網頁中的 Bug

    def switch_bet(self, amount: int):
        self._current_bet = amount

    def read_balance(self) -> int:
        return self._balance

    def spin(self):
        if self._balance < self._current_bet:
            raise RuntimeError("餘額不足")
        self._balance -= self._current_bet

    def wait_for_stop(self):
        import random, time as t
        reels = [random.choice(self.SYMBOLS) for _ in range(3)]
        key = tuple(reels)
        win = 0
        if key in self.PAYTABLE:
            win = self.PAYTABLE[key] * self._current_bet // 10
        elif reels[0] == "🍒" and reels[1] == "🍒":
            win = 2 * self._current_bet // 10

        self._spin_count += 1
        self._last_win = win

        # Bug：第 7 次只入帳一半
        actual_credit = win
        if self._inject_bug and self._spin_count == 7 and win > 0:
            actual_credit = win // 2

        self._balance += actual_credit
        t.sleep(0.05)

    def read_win(self) -> int:
        return self._last_win

    def read_bet(self) -> int:
        return self._current_bet

    def close(self):
        pass


# ═══════════════════════════════════════════════════════════
#  主測試流程
# ═══════════════════════════════════════════════════════════

def run_tests(driver, bet_amount: int = 20, run_count: int = 10) -> list[TestRecord]:
    records = []

    # 步驟 1：切換 bet
    driver.switch_bet(bet_amount)
    print(f"\n  押注設定：{bet_amount}")
    print(f"  {'項次':<5} {'資產(前)':<10} {'押注':<6} {'贏分':<8} {'資產(後)':<10} {'預期':<10} {'結果':<6} 原因")
    print("  " + "─" * 75)

    for i in range(1, run_count + 1):
        rec = TestRecord()
        rec.index = i
        rec.test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 步驟 2：讀取資產（前）
        rec.balance_before = driver.read_balance()

        # 餘額不足 edge case
        if rec.balance_before < bet_amount:
            rec.bet = bet_amount
            rec.win_displayed = 0
            rec.balance_after = rec.balance_before
            rec.pass_fail = "SKIP"
            rec.fail_reason = "餘額不足，跳過此次"
            records.append(rec)
            print(f"  {i:<5} {rec.balance_before:<10} {'─':<6} {'─':<8} {'─':<10} {'─':<10} SKIP  餘額不足")
            continue

        # 步驟 3：點擊 spin
        driver.spin()

        # 步驟 4：確認停輪
        driver.wait_for_stop()

        # 步驟 5：讀取贏分與資產（後）
        rec.win_displayed = driver.read_win()
        rec.bet = driver.read_bet()
        rec.balance_after = driver.read_balance()

        # 步驟 6：金流驗證
        rec.validate()
        records.append(rec)

        status_icon = "✓" if rec.pass_fail == "PASS" else "✗"
        print(f"  {i:<5} {rec.balance_before:<10} {rec.bet:<6} {rec.win_displayed:<8} "
              f"{rec.balance_after:<10} {rec.expected_balance:<10} "
              f"{status_icon} {rec.pass_fail:<4} {rec.fail_reason}")

    return records


# ═══════════════════════════════════════════════════════════
#  累積金流分析（資深 QA 額外驗證）
# ═══════════════════════════════════════════════════════════

def analyze_cumulative_flow(records: list[TestRecord]) -> dict:
    """
    累積金流分析：
    初始資產 + 總贏分 - 總押注 == 最終資產
    單次 PASS 不代表累積也正確
    """
    valid = [r for r in records if r.pass_fail in ("PASS", "FAIL")]
    if not valid:
        return {}

    initial = valid[0].balance_before
    final = valid[-1].balance_after
    total_bet = sum(r.bet for r in valid)
    total_win = sum(r.win_displayed for r in valid)
    expected_final = initial - total_bet + total_win
    cumulative_ok = (final == expected_final)

    return {
        "初始資產": initial,
        "最終資產": final,
        "總押注": total_bet,
        "總贏分": total_win,
        "預期最終資產": expected_final,
        "累積金流正確": "✓ PASS" if cumulative_ok else f"✗ FAIL（差 {final - expected_final:+d}）",
    }


# ═══════════════════════════════════════════════════════════
#  Excel 輸出
# ═══════════════════════════════════════════════════════════

def export_excel(records: list[TestRecord], summary: dict, path: str):
    wb = openpyxl.Workbook()

    # ── Sheet 1：詳細測試結果 ──
    ws = wb.active
    ws.title = "測試結果"

    PURPLE = "5B3FA0"
    LIGHT_PURPLE = "D4C5EE"
    GREEN = "C6EFCE"
    RED = "FFC7CE"
    YELLOW = "FFEB9C"
    WHITE = "FFFFFF"
    GRAY = "F2F2F2"

    thin = Side(style='thin', color='CCCCCC')
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)

    def hdr_cell(cell, val, bg=PURPLE):
        cell.value = val
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", start_color=bg)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = bd

    def data_cell(cell, val, bg=WHITE, bold=False, color="000000"):
        cell.value = val
        cell.font = Font(name="Arial", bold=bold, color=color)
        cell.fill = PatternFill("solid", start_color=bg)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = bd

    # 大標題
    ws.merge_cells("A1:I1")
    c = ws["A1"]
    c.value = "Slot 遊戲自動化測試報告"
    c.font = Font(name="Arial", bold=True, size=14, color="FFFFFF")
    c.fill = PatternFill("solid", start_color=PURPLE)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    # 欄位標題
    headers = ["項次","測試時間","玩家資產(前)","押注","遊戲贏分","玩家資產(後)","預期資產","測試結果","失敗原因"]
    for col, h in enumerate(headers, 1):
        hdr_cell(ws.cell(2, col), h)
    ws.row_dimensions[2].height = 22

    # 資料
    for idx, r in enumerate(records):
        row = idx + 3
        bg = GRAY if idx % 2 == 0 else WHITE

        result_bg = {"PASS": GREEN, "FAIL": RED, "SKIP": YELLOW}.get(r.pass_fail, WHITE)
        result_color = {"PASS": "375623", "FAIL": "9C0006", "SKIP": "7D4F00"}.get(r.pass_fail, "000000")

        data_cell(ws.cell(row, 1), r.index, bg)
        data_cell(ws.cell(row, 2), r.test_time, bg)
        data_cell(ws.cell(row, 3), r.balance_before, bg)
        data_cell(ws.cell(row, 4), r.bet, bg)
        data_cell(ws.cell(row, 5), r.win_displayed, bg)
        data_cell(ws.cell(row, 6), r.balance_after, bg)
        data_cell(ws.cell(row, 7), r.expected_balance if r.expected_balance else "-", bg)
        data_cell(ws.cell(row, 8), r.pass_fail, result_bg, bold=True, color=result_color)
        data_cell(ws.cell(row, 9), r.fail_reason, result_bg if r.pass_fail != "PASS" else bg)
        ws.row_dimensions[row].height = 20

    # 欄寬
    for i, w in enumerate([6,22,14,8,10,14,12,10,30], 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── Sheet 2：累積金流分析 ──
    ws2 = wb.create_sheet("金流分析")
    ws2.merge_cells("A1:C1")
    c2 = ws2["A1"]
    c2.value = "累積金流分析"
    c2.font = Font(name="Arial", bold=True, size=13, color="FFFFFF")
    c2.fill = PatternFill("solid", start_color=PURPLE)
    c2.alignment = Alignment(horizontal="center")
    ws2.row_dimensions[1].height = 28

    pass_count = sum(1 for r in records if r.pass_fail == "PASS")
    fail_count = sum(1 for r in records if r.pass_fail == "FAIL")
    skip_count = sum(1 for r in records if r.pass_fail == "SKIP")

    stats = [
        ("PASS 次數", pass_count),
        ("FAIL 次數", fail_count),
        ("SKIP 次數", skip_count),
        ("", ""),
    ] + [(k, v) for k, v in summary.items()]

    for row_i, (k, v) in enumerate(stats, 2):
        if not k:
            continue
        c_k = ws2.cell(row_i, 1)
        c_v = ws2.cell(row_i, 2)
        c_k.value = k
        c_v.value = v
        c_k.font = Font(name="Arial", bold=True)
        c_k.fill = PatternFill("solid", start_color=LIGHT_PURPLE)
        c_k.alignment = Alignment(horizontal="left", vertical="center")
        c_k.border = bd

        is_fail_row = ("FAIL" in str(v) or "差" in str(v))
        c_v.fill = PatternFill("solid", start_color=RED if is_fail_row else GREEN)
        c_v.font = Font(name="Arial", bold=True,
                        color="9C0006" if is_fail_row else "375623")
        c_v.alignment = Alignment(horizontal="center", vertical="center")
        c_v.border = bd
        ws2.row_dimensions[row_i].height = 22

    ws2.column_dimensions["A"].width = 20
    ws2.column_dimensions["B"].width = 25

    wb.save(path)
    print(f"\n  [✓] Excel 已儲存：{path}")


# ═══════════════════════════════════════════════════════════
#  主程式
# ═══════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  Slot 遊戲自動化測試（資深 QA 版）")
    print("=" * 60)

    HTML_PATH = "/mnt/user-data/outputs/slot_game.html"

    # 選擇驅動：有 Selenium + ChromeDriver 就用真實網頁，否則用 Mock
    try:
        if SELENIUM_AVAILABLE:
            driver = SlotGameDriver(HTML_PATH)
            print("\n  [模式] Selenium 真實網頁自動化")
        else:
            raise Exception("No selenium")
    except Exception:
        driver = MockSlotGameDriver()
        print("\n  [模式] Mock 模擬驅動（安裝 selenium+chromedriver 可測真實網頁）")

    try:
        records = run_tests(driver, bet_amount=20, run_count=10)
    finally:
        driver.close()

    # 累積金流分析
    summary = analyze_cumulative_flow(records)
    print("\n  ── 累積金流分析 ──")
    for k, v in summary.items():
        print(f"  {k:<14} {v}")

    # 統計
    pass_c = sum(1 for r in records if r.pass_fail == "PASS")
    fail_c = sum(1 for r in records if r.pass_fail == "FAIL")
    print(f"\n  結果：PASS {pass_c}/10　FAIL {fail_c}/10")

    if fail_c > 0:
        print("\n  ── 發現的 Bug ──")
        for r in records:
            if r.pass_fail == "FAIL":
                print(f"  第 {r.index} 次：{r.fail_reason}")

    # 輸出 Excel
    output_path = "/mnt/user-data/outputs/slot_test_result_senior.xlsx"
    export_excel(records, summary, output_path)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()