"""Flask web dashboard for AI Investment Signals system."""
import sys
import os
import json
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder="templates", static_folder="static")

# ── Mock data generators (work without API keys) ──────────────────────────────

def _mock_signals():
    events = [
        {"event": "US 25% Tariffs on Chinese Semiconductors", "type": "TARIFF_POLICY",
         "sentiment": "negative", "score": -0.82, "impact": "bearish",
         "sectors": ["semiconductor", "technology"], "urgency": "high",
         "summary": "美國對中國半導體加徵25%關稅，衝擊全球供應鏈", "date": _days_ago(0)},
        {"event": "Fed Raises Rates by 50bps", "type": "INTEREST_RATE",
         "sentiment": "negative", "score": -0.61, "impact": "bearish",
         "sectors": ["finance", "real estate"], "urgency": "high",
         "summary": "聯準會升息50基點，壓制成長股估值", "date": _days_ago(1)},
        {"event": "$52B CHIPS Act Subsidy Approved", "type": "GOVERNMENT_SUBSIDY",
         "sentiment": "positive", "score": 0.78, "impact": "bullish",
         "sectors": ["semiconductor", "manufacturing"], "urgency": "medium",
         "summary": "晶片法案補貼通過，本土半導體製造獲益", "date": _days_ago(1)},
        {"event": "China Retaliates with 30% EV Tariffs", "type": "TARIFF_POLICY",
         "sentiment": "negative", "score": -0.70, "impact": "bearish",
         "sectors": ["consumer", "manufacturing"], "urgency": "high",
         "summary": "中國報復性關稅衝擊美國電動車出口", "date": _days_ago(2)},
        {"event": "New AI Regulation Bill in EU", "type": "AI_REGULATION",
         "sentiment": "neutral", "score": -0.25, "impact": "neutral",
         "sectors": ["technology"], "urgency": "medium",
         "summary": "歐盟 AI 法規出台，科技公司需增加合規成本", "date": _days_ago(2)},
        {"event": "US-Japan Trade Deal Signed", "type": "TRADE_AGREEMENT",
         "sentiment": "positive", "score": 0.65, "impact": "bullish",
         "sectors": ["manufacturing", "technology"], "urgency": "medium",
         "summary": "美日貿易協議強化供應鏈韌性", "date": _days_ago(3)},
        {"event": "TSMC Supply Chain Disruption Alert", "type": "SUPPLY_CHAIN_DISRUPTION",
         "sentiment": "negative", "score": -0.55, "impact": "bearish",
         "sectors": ["semiconductor"], "urgency": "high",
         "summary": "台積電供應鏈出現短缺警示", "date": _days_ago(3)},
    ]
    return events


def _mock_strategy():
    return {
        "stance": "bearish",
        "risk": "high",
        "expected_return": "-5% to +8%",
        "stop_loss": 8.0,
        "horizon": "2-4 weeks",
        "actions": [
            {"action": "SELL", "asset": "NVDA", "pct": 25,
             "rationale": "減持曝險於中國供應鏈的半導體股"},
            {"action": "BUY",  "asset": "INTC", "pct": 20,
             "rationale": "增持受益於本土製造補貼的企業"},
            {"action": "BUY",  "asset": "TSM",  "pct": 15,
             "rationale": "台積電長期受益於供應鏈重組"},
            {"action": "HOLD", "asset": "AAPL", "pct": 15,
             "rationale": "觀察蘋果供應鏈調整進度"},
            {"action": "SELL", "asset": "AMD",  "pct": 10,
             "rationale": "短期避開中國曝險較高標的"},
        ],
        "risks": ["中美關係持續惡化", "聯準會進一步升息", "台海地緣政治風險"],
    }


def _mock_backtest():
    """Generate realistic-looking portfolio vs benchmark time series."""
    days = 756  # ~3 years trading days
    base_date = datetime.today() - timedelta(days=days)
    dates = [
        (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days)
        if (base_date + timedelta(days=i)).weekday() < 5
    ][:days]

    capital = 1_000_000
    bench_capital = 1_000_000
    portfolio, benchmark = [capital], [bench_capital]

    random.seed(42)
    for _ in range(len(dates) - 1):
        # Strategy: slightly higher return, higher vol
        r = random.gauss(0.00055, 0.012)
        b = random.gauss(0.00040, 0.010)
        portfolio.append(portfolio[-1] * (1 + r))
        benchmark.append(benchmark[-1] * (1 + b))

    total_ret = (portfolio[-1] / portfolio[0] - 1) * 100
    bench_ret = (benchmark[-1] / benchmark[0] - 1) * 100

    # Calculate drawdown series
    import numpy as np
    p = [v / portfolio[0] for v in portfolio]
    roll_max = []
    cur_max = p[0]
    for v in p:
        cur_max = max(cur_max, v)
        roll_max.append(cur_max)
    drawdown = [(p[i] - roll_max[i]) / roll_max[i] * 100 for i in range(len(p))]

    return {
        "dates": dates[:len(portfolio)],
        "portfolio": [round(v, 2) for v in portfolio],
        "benchmark": [round(v, 2) for v in benchmark],
        "drawdown": [round(d, 4) for d in drawdown],
        "metrics": {
            "total_return": round(total_ret, 2),
            "annualized_return": round(total_ret / 3, 2),
            "volatility": 18.4,
            "sharpe": 0.912,
            "max_drawdown": round(min(drawdown), 2),
            "win_rate": 63.6,
            "benchmark_return": round(bench_ret, 2),
            "alpha": round(total_ret - bench_ret, 2),
            "total_trades": 47,
        },
    }


def _days_ago(n):
    return (datetime.today() - timedelta(days=n)).strftime("%Y-%m-%d")


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/signals")
def api_signals():
    return jsonify(_mock_signals())


@app.route("/api/strategy")
def api_strategy():
    return jsonify(_mock_strategy())


@app.route("/api/backtest")
def api_backtest():
    return jsonify(_mock_backtest())


@app.route("/api/summary")
def api_summary():
    signals = _mock_signals()
    bearish = sum(1 for s in signals if s["sentiment"] == "negative")
    bullish = sum(1 for s in signals if s["sentiment"] == "positive")
    return jsonify({
        "total_signals": len(signals),
        "bearish": bearish,
        "bullish": bullish,
        "neutral": len(signals) - bearish - bullish,
        "high_urgency": sum(1 for s in signals if s["urgency"] == "high"),
        "market_stance": "BEARISH",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })


if __name__ == "__main__":
    print("\n🚀 AI Investment Dashboard 啟動中...")
    print("   開啟瀏覽器前往: http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
