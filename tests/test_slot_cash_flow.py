"""
Test ID:    TC-001
Test Title: Slot 遊戲單局金流驗證（10 連局）
Test Steps:
  1. 從 data/test_config.json 讀取押注金額與執行次數
  2. 切換 bet 至設定金額
  3. 讀取玩家資產（前）
  4. 點擊 SPIN 按鈕進行遊戲
  5. 等待停輪（動態等待：spin 按鈕恢復可點擊）
  6. 讀取遊戲贏分與玩家資產（後）
  7. 金流驗證：資產(前) - 押注 + 贏分 == 資產(後)
  重複步驟 3~7 共 N 次
Expected Result:
  每局金流公式成立 → PASS；金流異常 → FAIL 並記錄差異值；餘額不足 → SKIP

Test ID:    TC-002
Test Title: Slot 遊戲累積金流驗證
Test Steps:
  1. 彙整所有 PASS/FAIL 局的紀錄
  2. 計算：初始資產 + 總贏分 - 總押注 == 最終資產
Expected Result:
  累積金流公式成立 → PASS；不符 → FAIL 並顯示差異值
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import json
from datetime import datetime

from utils.test_record import TestRecord
from utils.report_generator import analyze_cumulative_flow, export_excel

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "test_config.json")


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _create_driver():
    try:
        from pages.slot_game_page import SlotGamePage
        driver = SlotGamePage(headless=False)
        driver.open()
        print("  [模式] Selenium 真實網頁自動化")
        return driver
    except Exception:
        from utils.mock_slot_page import MockSlotPage
        driver = MockSlotPage()
        driver.open()
        print("  [模式] Mock 模擬驅動")
        return driver


def run_cash_flow_test() -> list:
    cfg          = _load_config()
    bet_amount   = cfg["bet_amount"]
    total_rounds = cfg["total_rounds"]
    records      = []

    driver = _create_driver()
    try:
        driver.switch_bet(bet_amount)
        print(f"\n  押注設定：{bet_amount}")
        print(f"  {'項次':<5} {'資產(前)':<10} {'押注':<6} {'贏分':<8} {'資產(後)':<10} {'預期':<10} {'結果':<6} 原因")
        print("  " + "─" * 75)

        for i in range(1, total_rounds + 1):
            rec           = TestRecord()
            rec.index     = i
            rec.test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rec.balance_before = driver.read_balance()

            if rec.balance_before < bet_amount:
                rec.bet           = bet_amount
                rec.win_displayed = 0
                rec.balance_after = rec.balance_before
                rec.pass_fail     = "SKIP"
                rec.fail_reason   = "餘額不足，跳過"
                records.append(rec)
                print(f"  {i:<5} {rec.balance_before:<10} {'─':<6} {'─':<8} {'─':<10} {'─':<10} SKIP  餘額不足")
                continue

            driver.click_spin()
            driver.wait_for_spin_complete()

            rec.win_displayed = driver.read_win()
            rec.bet           = driver.read_current_bet()
            rec.balance_after = driver.read_balance()
            rec.validate()
            records.append(rec)

            icon = "✓" if rec.pass_fail == "PASS" else "✗"
            print(f"  {i:<5} {rec.balance_before:<10} {rec.bet:<6} {rec.win_displayed:<8} "
                  f"{rec.balance_after:<10} {rec.expected_balance:<10} "
                  f"{icon} {rec.pass_fail:<4} {rec.fail_reason}")
    finally:
        driver.close()

    summary = analyze_cumulative_flow(records)
    print("\n  ── TC-002 累積金流分析 ──")
    for k, v in summary.items():
        print(f"  {k:<16} {v}")

    pass_c = sum(1 for r in records if r.pass_fail == "PASS")
    fail_c = sum(1 for r in records if r.pass_fail == "FAIL")
    print(f"\n  結果：PASS {pass_c}/{total_rounds}　FAIL {fail_c}/{total_rounds}")

    if fail_c > 0:
        print("\n  ── 發現的 Bug ──")
        for r in records:
            if r.pass_fail == "FAIL":
                print(f"  第 {r.index} 次：{r.fail_reason}")

    filename = f"slot_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path     = export_excel(records, summary, filename)
    print(f"\n  [✓] 報表已儲存：{path}")

    return records


if __name__ == "__main__":
    print("=" * 60)
    print("  Slot 遊戲自動化測試")
    print("=" * 60)
    run_cash_flow_test()
    print("=" * 60)
