"""LINE Bot integration — push notifications and webhook server.

Two components:
1. LineBotNotifier  — pushes messages to a LINE user/group.
2. LineBotWebhook   — Flask server that receives LINE events (for interactive queries).
"""
import logging
import os

import requests
from flask import Flask, request, abort

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LINE_USER_ID
from ai_analyzer.strategy_generator import InvestmentStrategy
from backtester.performance_metrics import PerformanceReport

logger = logging.getLogger(__name__)

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


class LineBotNotifier:
    """Sends push messages to a LINE user / group."""

    def __init__(
        self,
        access_token: str = LINE_CHANNEL_ACCESS_TOKEN,
        user_id: str = LINE_USER_ID,
    ):
        self.access_token = access_token
        self.user_id = user_id

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

    def send_text(self, text: str) -> bool:
        """Send a plain text message."""
        if not self.access_token or not self.user_id:
            logger.warning(
                "LINE credentials not configured — printing to console instead.\n%s", text
            )
            print("\n" + "="*60)
            print("[LINE Bot 模擬推播]")
            print("="*60)
            print(text)
            print("="*60 + "\n")
            return False

        payload = {
            "to": self.user_id,
            "messages": [{"type": "text", "text": text}],
        }
        try:
            resp = requests.post(LINE_PUSH_URL, json=payload, headers=self._headers(), timeout=10)
            resp.raise_for_status()
            logger.info("LINE push sent successfully.")
            return True
        except Exception as exc:
            logger.error("LINE push failed: %s", exc)
            return False

    def send_strategy_alert(
        self, strategy: InvestmentStrategy, performance: PerformanceReport
    ) -> bool:
        """Format and push strategy + performance alert."""
        perf_summary = (
            f"\n📊 回測績效\n"
            f"  年化報酬: {performance.annualized_return_pct:+.2f}%\n"
            f"  最大回撤: {performance.max_drawdown_pct:.2f}%\n"
            f"  夏普比率: {performance.sharpe_ratio:.3f}\n"
            f"  勝率    : {performance.win_rate_pct:.1f}%\n"
            f"  Alpha   : {performance.alpha_pct:+.2f}%"
        )
        message = strategy.to_line_message() + perf_summary
        return self.send_text(message)

    def send_signal_summary(self, signals: list[dict]) -> bool:
        """Push a summary of detected signals."""
        if not signals:
            return self.send_text("✅ 目前無重大市場訊號。")
        lines = ["🔔 最新市場訊號摘要\n"]
        for s in signals[:5]:
            lines.append(
                f"• [{s.get('event_type','?')}] {s.get('summary','')}\n"
                f"  情緒: {s.get('sentiment','')} | 影響: {s.get('sectors', [])}\n"
            )
        return self.send_text("\n".join(lines))


class LineBotWebhook:
    """Flask-based webhook server for LINE interactive messages."""

    def __init__(self, notifier: LineBotNotifier = None):
        self.app = Flask(__name__)
        self.notifier = notifier or LineBotNotifier()
        self._register_routes()

    def _register_routes(self):
        @self.app.route("/webhook", methods=["POST"])
        def webhook():
            # Signature validation
            signature = request.headers.get("X-Line-Signature", "")
            body = request.get_data(as_text=True)
            if not self._verify_signature(body, signature):
                abort(400)

            events = request.json.get("events", [])
            for event in events:
                self._handle_event(event)
            return "OK"

        @self.app.route("/health", methods=["GET"])
        def health():
            return {"status": "ok", "service": "AI Investment Signals LINE Bot"}

    def _verify_signature(self, body: str, signature: str) -> bool:
        """Verify LINE webhook signature using HMAC-SHA256."""
        import base64
        import hashlib
        import hmac

        if not LINE_CHANNEL_SECRET:
            return True  # Skip validation in dev mode

        hash_ = hmac.new(
            LINE_CHANNEL_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        expected = base64.b64encode(hash_).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    def _handle_event(self, event: dict):
        if event.get("type") != "message":
            return
        msg_type = event.get("message", {}).get("type")
        if msg_type != "text":
            return

        user_text = event["message"]["text"].strip().lower()
        reply_token = event.get("replyToken", "")

        # Simple command parsing
        if "狀態" in user_text or "status" in user_text:
            reply = "系統正常運作中。輸入 '分析' 以獲取最新投資訊號。"
        elif "分析" in user_text or "signal" in user_text:
            reply = "🔄 正在分析市場訊號，請稍候…"
        elif "說明" in user_text or "help" in user_text:
            reply = (
                "📖 AI 投資預警系統\n"
                "指令:\n"
                "  分析 — 觸發市場訊號分析\n"
                "  狀態 — 查看系統狀態\n"
                "  說明 — 顯示此說明"
            )
        else:
            reply = "請輸入 '說明' 查看可用指令。"

        self._reply(reply_token, reply)

    def _reply(self, reply_token: str, text: str):
        if not LINE_CHANNEL_ACCESS_TOKEN:
            logger.info("(dev) LINE reply: %s", text)
            return
        payload = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text}],
        }
        try:
            requests.post(
                LINE_REPLY_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                },
                timeout=5,
            )
        except Exception as exc:
            logger.error("LINE reply failed: %s", exc)

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        logger.info("Starting LINE Bot webhook on port %d", port)
        self.app.run(host=host, port=port, debug=debug)
