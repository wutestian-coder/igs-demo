# Slot 遊戲自動化測試

品檢軟體工程師初試作業 — Slot 遊戲金流自動化測試實作

## 專案結構

```
├── pages/
│   └── slot_game_page.py      # Page Object，封裝所有 UI 操作與 selector
├── tests/
│   ├── test_slot_cash_flow.py # UI 層測試（TC-001、TC-002）
│   └── test_slot_api.py       # API 層測試（TC-API-001、TC-API-002）
├── utils/
│   ├── image_utils.py         # OpenCV 共用函數（截圖轉換、幀差比對）
│   ├── api_client.py          # WebSocket 客戶端與 Mock 實作
│   ├── mock_slot_page.py      # UI Mock 驅動，供無 ChromeDriver 環境使用
│   ├── report_generator.py    # Excel 報表產生器
│   └── test_record.py         # 測試紀錄資料結構與金流驗證邏輯
├── data/
│   └── test_config.json       # 測試參數（押注金額、執行次數、ws_url）
├── config/
│   └── settings.py            # 路徑、逾時、OpenCV 閾值設定
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

**UI 層測試（Selenium + OpenCV）**
```bash
python tests/test_slot_cash_flow.py
```

**API 層測試（WebSocket）**
```bash
python tests/test_slot_api.py
```

沒有 ChromeDriver 或 WebSocket 連線的環境會自動切換為 Mock 模式執行。

報表輸出至 `reports/` 目錄。

## 測試架構

### 兩層測試策略

```
API 層（test_slot_api.py）
  └── 直接打 WebSocket，驗證後台金流邏輯
      快速、無需瀏覽器、適合大量回歸測試

UI 層（test_slot_cash_flow.py）
  └── Selenium 控制瀏覽器 + OpenCV 視覺確認
      驗證畫面顯示與後台資料一致
```

API 層出錯 → 後台邏輯問題
UI 層出錯但 API 層正常 → 前端顯示問題

### TC-001 / TC-API-001 單局金流驗證

每次 spin 執行以下驗證：

```
資產（後）= 資產（前）- 押注 + 贏分
```

任何一局不符合此公式即標記為 **FAIL** 並記錄差異值。

### TC-002 / TC-API-002 累積金流驗證

10 局結束後額外驗算：

```
最終資產 = 初始資產 - 總押注 + 總贏分
```

單局均 PASS 不代表累積正確，此驗證獨立進行。

## OpenCV 視覺停輪偵測

傳統 DOM 等待（spin 按鈕恢復可點擊）只確認後台計算完成，無法保證轉軸動畫已結束。

本專案使用 **Frame Differencing（幀差法）** 確認視覺層停輪：

```
每 150ms 截取轉軸區域截圖
    ↓
cv2.absdiff() 計算兩幀像素差
    ↓
平均差值 < 1.0 連續 2 次 → 判定轉軸靜止
```

相關設定在 `config/settings.py`：
```python
REEL_STOP_THRESHOLD = 1.0   # 像素差閾值
REEL_STOP_INTERVAL  = 0.15  # 取樣間隔（秒）
```

取樣間隔刻意設為 150ms（非動畫週期 100ms 的整數倍），避免 Aliasing 誤判。

## 測試設計重點

- **視覺停輪確認**：OpenCV Frame Differencing，偵測畫面真正靜止而非只看 DOM 狀態
- **兩層測試分離**：API 層驗邏輯，UI 層驗顯示，出錯時快速定位問題層級
- **動態等待**：所有等待均基於元件狀態或畫面變化，不使用固定 sleep
- **POM 架構**：selector 集中於 `pages/`，測試邏輯與 UI 操作完全分離
- **測試資料外部化**：所有參數從 `data/test_config.json` 讀取

## WebSocket API 設定

有真實遊戲伺服器時，在 `data/test_config.json` 填入 `ws_url`：

```json
{
  "bet_amount": 20,
  "total_rounds": 10,
  "ws_url": "wss://your-game-server/ws"
}
```

空字串自動使用 Mock 模式。

## 報表範例

`sample_reports/` 內含實際執行結果，第 7 局觸發金流 Bug（贏分顯示 4，實際入帳 2，差值 -2）。
