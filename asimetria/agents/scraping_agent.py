import feedparser
import yfinance as yf
import logging
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser

from agents.models import NewsItem
from config.settings import Settings

logger = logging.getLogger(__name__)


class ScrapingAgent:
    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch_news(self) -> list:
        """Obtiene noticias de todos los feeds RSS configurados."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.settings.LOOKBACK_HOURS)
        all_items = []

        for feed_url in self.settings.RSS_FEEDS:
            try:
                items = self._parse_feed(feed_url, cutoff_time)
                logger.info(f"Feed '{feed_url[:50]}': {len(items)} noticias recientes")
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"Error al procesar feed '{feed_url[:50]}': {e}")

        unique_items = self._deduplicate(all_items)
        logger.info(
            f"Total noticias únicas (últimas {self.settings.LOOKBACK_HOURS}h): {len(unique_items)}"
        )
        return unique_items

    def _parse_feed(self, url: str, cutoff_time: datetime) -> list:
        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries:
            try:
                published_str = entry.get("published") or entry.get("updated") or ""
                pub_dt = self._parse_date(published_str)

                if pub_dt and pub_dt < cutoff_time:
                    continue

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()

                if not title or not link:
                    continue

                summary = entry.get("summary", "") or entry.get("description", "")
                feed_title = getattr(feed.feed, "title", url)

                items.append(
                    NewsItem(
                        title=title[:500],
                        summary=summary[:1200],
                        url=link,
                        source=feed_title,
                        published_at=published_str,
                        raw_content=(title + " " + summary)[:1500],
                    )
                )
            except Exception as e:
                logger.debug(f"Error parseando entrada: {e}")
                continue

        return items

    def _parse_date(self, date_str: str):
        if not date_str:
            return None
        try:
            dt = dateparser.parse(date_str)
            if dt and dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def _deduplicate(self, items: list) -> list:
        seen_urls = set()
        unique = []
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique.append(item)
        return unique

    def get_market_context(self, tickers: list) -> dict:
        """Obtiene precio actual y variación 24h de los activos monitoreados."""
        context = {}
        for ticker in tickers:
            try:
                asset = yf.Ticker(ticker)
                hist = asset.history(period="2d", interval="1h")
                if hist.empty:
                    continue

                current = float(hist["Close"].iloc[-1])
                lookback = min(24, len(hist) - 1)
                prev = float(hist["Close"].iloc[-lookback - 1]) if lookback > 0 else current
                change_pct = ((current - prev) / prev * 100) if prev != 0 else 0.0

                context[ticker] = {
                    "price": round(current, 4),
                    "change_24h_pct": round(change_pct, 2),
                    "trend": "alcista" if change_pct > 0 else "bajista",
                }
            except Exception as e:
                logger.debug(f"Error obteniendo datos de {ticker}: {e}")

        return context
