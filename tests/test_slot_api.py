"""
Test ID:    TC-API-001
Test Title: Slot 遊戲 API 層單局金流驗證（10 連局）
Test Steps:
  1. 從 data/test_config.json 讀取押注金額、執行次數、ws_url
  2. 建立 WebSocket 連線，取得初始資產
  3. 發送 spin 請求（含押注金額）
  4. 接收伺服器回應（轉軸結果、贏分、餘額）
  5. 金流驗證：資產(前) - 押注 + 贏分 == 資產(後)
  重複步驟 3~5 共 N 次
Expected Result:
  每局金流公式成立 → PASS；金流異常 → FAIL 並記錄差異值；餘額不足 → SKIP

Test ID:    TC-API-002
Test Title: Slot 遊戲 API 層累積金流驗證
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
from utils.api_client import SlotApiClient, MockSlotApiClient
from utils.report_generator import analyze_cumulative_flow, export_excel

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "test_config.json")


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _create_client(ws_url: str):
    if ws_url:
        try:
            client = SlotApiClient(ws_url)
            client.connect()
            print("  [模式] WebSocket 真實 API 測試")
            return client
        except Exception as e:
            print(f"  [警告] WebSocket 連線失敗（{e}），切換為 Mock 模式")
    client = MockSlotApiClient()
    print("  [模式] Mock API 測試")
    return client


def run_api_cash_flow_test() -> list:
    cfg          = _load_config()
    bet_amount   = cfg["bet_amount"]
    total_rounds = cfg["total_rounds"]
    ws_url       = cfg.get("ws_url", "")
    records      = []

    client  = _create_client(ws_url)
    balance = client.connect()["balance"]

    try:
        print(f"\n  押注設定：{bet_amount}")
        print(f"  初始資產：{balance}")
        print(f"  {'項次':<5} {'資產(前)':<10} {'押注':<6} {'贏分':<8} {'資產(後)':<10} {'預期':<10} {'結果':<6} 原因")
        print("  " + "─" * 75)

        for i in range(1, total_rounds + 1):
            rec                = TestRecord()
            rec.index          = i
            rec.test_time      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rec.balance_before = balance

            if balance < bet_amount:
                rec.bet           = bet_amount
                rec.win_displayed = 0
                rec.balance_after = balance
                rec.pass_fail     = "SKIP"
                rec.fail_reason   = "餘額不足，跳過"
                records.append(rec)
                print(f"  {i:<5} {balance:<10} {'─':<6} {'─':<8} {'─':<10} {'─':<10} SKIP  餘額不足")
                continue

            resp              = client.spin(bet_amount)
            rec.win_displayed = resp["win"]
            rec.bet           = bet_amount
            rec.balance_after = resp["balance"]
            balance           = resp["balance"]
            rec.validate()
            records.append(rec)

            icon = "✓" if rec.pass_fail == "PASS" else "✗"
            print(f"  {i:<5} {rec.balance_before:<10} {rec.bet:<6} {rec.win_displayed:<8} "
                  f"{rec.balance_after:<10} {rec.expected_balance:<10} "
                  f"{icon} {rec.pass_fail:<4} {rec.fail_reason}")
    finally:
        client.close()

    summary = analyze_cumulative_flow(records)
    print("\n  ── TC-API-002 累積金流分析 ──")
    for k, v in summary.items():
        print(f"  {k:<16} {v}")

    pass_c = sum(1 for r in records if r.pass_fail == "PASS")
    fail_c = sum(1 for r in records if r.pass_fail == "FAIL")
    print(f"\n  結果：PASS {pass_c}/{total_rounds}　FAIL {fail_c}/{total_rounds}")

    filename = f"slot_api_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path     = export_excel(records, summary, filename)
    print(f"\n  [✓] 報表已儲存：{path}")

    return records


if __name__ == "__main__":
    print("=" * 60)
    print("  Slot 遊戲 API 自動化測試")
    print("=" * 60)
    run_api_cash_flow_test()
    print("=" * 60)
