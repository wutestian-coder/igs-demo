# Slot 遊戲自動化測試

品檢軟體工程師初試作業 — Slot 遊戲金流自動化測試實作

## 專案結構

```
├── pages/
│   └── slot_game_page.py     # Page Object，封裝所有 UI 操作與 selector
├── tests/
│   └── test_slot_cash_flow.py # 測試案例主程式（TC-001、TC-002）
├── utils/
│   ├── mock_slot_page.py      # Mock 驅動，供無 ChromeDriver 環境使用
│   ├── report_generator.py    # Excel 報表產生器
│   └── test_record.py         # 測試紀錄資料結構與金流驗證邏輯
├── data/
│   └── test_config.json       # 測試參數（押注金額、執行次數）
├── config/
│   └── settings.py            # 路徑與逾時設定
├── slot_game.html             # 測試用 Slot 遊戲（含注入 Bug）
└── sample_reports/
    └── *.xlsx                 # 測試報表範例
```

## 環境安裝

```bash
pip install -r requirements.txt
```

需要 Chrome 瀏覽器與對應版本的 ChromeDriver（Selenium 4.x 已內建自動管理）。

## 執行方式

```bash
python tests/test_slot_cash_flow.py
```

沒有 ChromeDriver 的環境會自動切換為 Mock 模式執行。

報表輸出至 `reports/` 目錄。

## 測試邏輯

### TC-001 單局金流驗證

每次 spin 執行以下驗證：

```
資產（後）= 資產（前）- 押注 + 贏分
```

任何一局不符合此公式即標記為 **FAIL** 並記錄差異值。

### TC-002 累積金流驗證

10 局結束後額外驗算：

```
最終資產 = 初始資產 - 總押注 + 總贏分
```

單局均 PASS 不代表累積正確，此驗證獨立進行。

## 測試設計重點

- **動態等待**：以 spin 按鈕狀態變化作為停輪信號，不使用固定 sleep
- **POM 架構**：selector 集中於 `pages/`，測試邏輯與 UI 操作完全分離
- **測試資料外部化**：押注金額與執行次數從 `data/test_config.json` 讀取

## 報表範例

`sample_reports/` 內含實際執行結果，第 7 局觸發金流 Bug（贏分顯示 4，實際入帳 2，差值 -2）。
