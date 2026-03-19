# AI 投資訊號預警與回測系統
### AI Investment Signals Warning & Backtesting System

> 結合社群訊號分析與 AI 工作流程之投資策略預警與回測系統設計
> ——以政策訊號與市場事件分析為例

---

## 系統架構 System Architecture

```
社群 / 新聞資料          Data Collection
        ↓
AI 情緒分析 (Claude)     Sentiment Analysis
        ↓
事件分類 (Claude)        Event Classification
        ↓
策略生成 (Claude)        Strategy Generation
        ↓
策略回測 (yfinance)      Backtesting (3-year historical)
        ↓
績效評估                 Performance Metrics
        ↓
LINE Bot 推播            LINE Bot Push Notification
```

## 核心模組 Modules

| 模組 | 路徑 | 功能 |
|------|------|------|
| 資料收集 | `data_collector/` | 新聞 (NewsAPI + RSS) & 社群訊號 (Twitter/X) |
| 情緒分析 | `ai_analyzer/sentiment_analyzer.py` | Claude AI 情緒評分 (-1 ~ +1) |
| 事件分類 | `ai_analyzer/event_classifier.py` | 11種事件類型 (關稅、利率、供應鏈…) |
| 策略生成 | `ai_analyzer/strategy_generator.py` | Claude AI 生成買賣策略 |
| 回測引擎 | `backtester/backtest_engine.py` | 3年歷史資料，月度再平衡 |
| 績效指標 | `backtester/performance_metrics.py` | 年化報酬、最大回撤、夏普比率、勝率 |
| LINE Bot | `line_bot/bot.py` | 推播通知 + Webhook 互動 |
| 主程式 | `main.py` | 完整 Pipeline 流程 |
| Demo | `demo/demo_run.py` | 展示用範例 |

## 快速開始 Quick Start

### 1. 安裝相依套件
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
```bash
cp .env.example .env
# 編輯 .env，填入 ANTHROPIC_API_KEY
```

### 3. 執行 Demo
```bash
python demo/demo_run.py
```

### 4. 執行完整 Pipeline
```bash
python main.py
```

### 5. 啟動 LINE Bot Webhook（選用）
```bash
python -c "
from line_bot import LineBotWebhook
LineBotWebhook().run(port=5000)
"
```

---

## 事件類型 Event Types

| 代碼 | 說明 |
|------|------|
| `TARIFF_POLICY` | 關稅政策 |
| `INTEREST_RATE` | 利率調整 |
| `TRADE_AGREEMENT` | 貿易協議 |
| `EXPORT_CONTROL` | 出口管制 |
| `GOVERNMENT_SUBSIDY` | 政府補貼 |
| `AI_REGULATION` | AI 法規 |
| `SUPPLY_CHAIN_DISRUPTION` | 供應鏈中斷 |
| `EARNINGS_SURPRISE` | 財報超預期 |
| `GEOPOLITICAL_TENSION` | 地緣政治緊張 |
| `COMMODITY_SHOCK` | 大宗商品衝擊 |

## 系統輸出範例 Sample Output

```
⚠️ AI 投資預警
📌 事件: 美國對中國半導體加徵25%關稅，衝擊全球供應鏈。
📊 整體立場: BEARISH
⚡ 風險等級: high
📈 預期報酬: -5% to +8%
🛑 停損: -8.0%
⏱  時間框架: 2-4 weeks

🎯 建議操作:
  🔴 SELL NVDA (25%) — 減持曝險於中國供應鏈的半導體股
  🟢 BUY  INTC (20%) — 增持受益於本土製造補貼的企業
  🟡 HOLD AAPL (15%) — 觀察蘋果供應鏈調整進度

📊 回測績效
  年化報酬: +14.23%
  最大回撤: -9.87%
  夏普比率: 0.912
  勝率    : 63.6%
  Alpha   : +5.41%
```

## 技術堆疊 Tech Stack

| 工具 | 角色 |
|------|------|
| Claude (Anthropic) | AI 情緒分析、事件分類、策略生成 |
| yfinance | 歷史股價資料 |
| pandas / numpy | 資料處理與績效計算 |
| Flask | LINE Bot Webhook 伺服器 |
| feedparser | RSS 新聞爬取 |
| NewsAPI | 新聞資料（選用） |
| Twitter API v2 | 社群訊號（選用，有 mock 替代）|

---

## 創新亮點 Innovation Highlights

這個系統比傳統量化回測多了一層「**事件驅動**」：

```
傳統: 技術指標 → 回測
本系統: 事件 → AI分析 → 市場影響 → 策略 → 回測
```

這是對沖基金（Hedge Fund）真實採用的 **Event-Driven Trading** 架構。
