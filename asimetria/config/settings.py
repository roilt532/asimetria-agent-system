import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        # ---- Credenciales requeridas ----
        self.GEMINI_API_KEY: str = os.environ["GEMINI_API_KEY"]
        self.TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
        self.TELEGRAM_CHAT_ID: str = os.environ["TELEGRAM_CHAT_ID"]

        # ---- Modelo LLM ----
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

        # ---- Comportamiento del pipeline ----
        self.MIN_CONFIDENCE: float = float(os.getenv("MIN_CONFIDENCE", "0.75"))
        self.LOOKBACK_HOURS: int = int(os.getenv("LOOKBACK_HOURS", "2"))
        self.SEND_SUMMARY: bool = os.getenv("SEND_SUMMARY", "false").lower() == "true"

        # ---- Lista negra personalizada (separada por comas en .env) ----
        self.CUSTOM_BLOCKLIST: list = [
            e.strip()
            for e in os.getenv("CUSTOM_BLOCKLIST", "").split(",")
            if e.strip()
        ]

        # ---- Fuentes RSS gratuitas (sin API key) ----
        self.RSS_FEEDS: list = [
            "https://finance.yahoo.com/rss/topfinstories",
            "https://finance.yahoo.com/rss/2.0/headline?s=BTC-USD&region=US&lang=en-US",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cryptonews.com/news/feed/",
            "https://cointelegraph.com/rss",
            "https://bitcoinist.com/feed/",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://www.cnbc.com/id/10001147/device/rss/rss.html",
            "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
        ]

        # ---- Tickers para contexto de mercado (via yfinance) ----
        self.MONITORED_TICKERS: list = [
            "BTC-USD",
            "ETH-USD",
            "SPY",
            "QQQ",
            "GLD",
        ]


# Singleton — se instancia al ejecutar el pipeline (requiere .env con credenciales)
settings = Settings()
