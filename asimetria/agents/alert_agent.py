import requests
import logging
from datetime import datetime, timezone

from agents.models import AnalysisResult
from config.settings import Settings

logger = logging.getLogger(__name__)

DIRECTION_LABEL = {
    "bullish": "ALCISTA",
    "bearish": "BAJISTA",
    "neutral": "NEUTRAL",
}

DIRECTION_ICON = {
    "bullish": "[SUBE]",
    "bearish": "[BAJA]",
    "neutral": "[~]",
}

MESSAGE_TEMPLATE = (
    "<b>ASIMETRIA — OPORTUNIDAD DETECTADA</b>\n"
    "\n"
    "<b>Activo:</b> {asset}\n"
    "<b>Señal:</b> {icon} {direction_label}\n"
    "<b>Confianza:</b> {confidence_pct}%\n"
    "<b>Publicado:</b> {published_at}\n"
    "<b>Fuente:</b> {source}\n"
    "\n"
    "<b>Titular:</b>\n"
    "{title}\n"
    "\n"
    "<b>Análisis:</b>\n"
    "{reasoning}\n"
    "\n"
    "<a href='{url}'>Ver noticia completa</a>"
)

SUMMARY_TEMPLATE = (
    "<b>Resumen Pipeline Asimetria</b>\n"
    "\n"
    "Noticias analizadas: <b>{total_news}</b>\n"
    "Oportunidades enviadas: <b>{opportunities}</b>\n"
    "\n"
    "<i>Ejecutado: {timestamp} UTC</i>"
)


class AlertAgent:
    def __init__(self, settings: Settings):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self._api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_opportunity(self, result: AnalysisResult) -> bool:
        """Envía una alerta de oportunidad asimétrica a Telegram."""
        direction = result.direction.lower()
        message = MESSAGE_TEMPLATE.format(
            asset=result.asset_mentioned or "MULTI-ACTIVO",
            icon=DIRECTION_ICON.get(direction, "[~]"),
            direction_label=DIRECTION_LABEL.get(direction, "NEUTRAL"),
            confidence_pct=int(result.confidence * 100),
            published_at=result.news_item.published_at or "N/A",
            source=result.news_item.source,
            title=result.news_item.title,
            reasoning=result.reasoning,
            url=result.news_item.url,
        )
        return self._send(message)

    def send_summary(self, total_news: int, opportunities: int) -> bool:
        """Envía un resumen del ciclo de ejecución."""
        message = SUMMARY_TEMPLATE.format(
            total_news=total_news,
            opportunities=opportunities,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        )
        return self._send(message)

    def _send(self, message: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(self._api_url, json=payload, timeout=30)
            resp.raise_for_status()
            logger.info("Alerta enviada a Telegram correctamente.")
            return True
        except requests.RequestException as e:
            logger.error(f"Error enviando alerta a Telegram: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Respuesta Telegram: {e.response.text}")
            return False
