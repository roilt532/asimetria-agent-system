import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from google import genai
from google.genai import types

from agents.models import AnalysisResult
from config.settings import Settings

logger = logging.getLogger(__name__)

DAILY_LOG_PATH = Path("data/daily_opportunities.json")

RANKING_SYSTEM_PROMPT = """Eres un analista cuantitativo experto en síntesis de señales de mercado asimétrico.

Recibirás un JSON con todas las oportunidades detectadas durante el día.
Tu misión: analizarlas, agruparlas por activo, rankearlas por potencial real y generar un resumen ejecutivo.

CRITERIOS DE RANKING (de mayor a menor peso):
1. Confianza promedio del activo (si hay múltiples señales del mismo activo, promediar)
2. Consistencia de dirección (varias señales en la misma dirección = mayor peso)
3. Relevancia e impacto potencial del catalizador
4. Momento del activo en el mercado

Responde EXCLUSIVAMENTE en JSON válido con esta estructura:
{
  "ranked_opportunities": [
    {
      "rank": 1,
      "asset": "BTC",
      "direction": "bullish",
      "avg_confidence": 0.88,
      "signal_count": 3,
      "key_catalysts": ["Catalizador principal en español", "Catalizador secundario"],
      "top_headline": "El titular más representativo del activo"
    }
  ],
  "market_sentiment": "alcista",
  "total_signals": 8,
  "summary_text": "Párrafo ejecutivo de 3-4 frases en español. Describe qué ocurrió hoy, qué activos destacaron y por qué representan oportunidades asimétricas."
}

Limita ranked_opportunities a máximo 5 activos (los de mayor potencial).
Valores permitidos para direction: bullish, bearish, neutral.
Valores permitidos para market_sentiment: alcista, bajista, mixto, neutral."""


class SummaryAgent:
    def __init__(self, settings: Settings):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def append_opportunity(self, result: AnalysisResult) -> None:
        """Añade una oportunidad al log acumulado del día."""
        DAILY_LOG_PATH.parent.mkdir(exist_ok=True)
        log = self._load_log()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Resetear si el log pertenece a un día anterior
        if log.get("date") != today:
            log = {"date": today, "opportunities": []}

        log["opportunities"].append({
            "title": result.news_item.title,
            "asset": result.asset_mentioned or "MULTI-ACTIVO",
            "direction": result.direction,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "source": result.news_item.source,
            "url": result.news_item.url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        DAILY_LOG_PATH.write_text(
            json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.debug(f"Oportunidad guardada en log diario: {result.asset_mentioned}")

    def generate_ranked_summary(self) -> dict | None:
        """
        Lee el log del día y genera un resumen rankeado con GPT-4o-mini.
        Devuelve None si no hay oportunidades registradas.
        """
        log = self._load_log()
        opportunities = log.get("opportunities", [])

        if not opportunities:
            logger.info("Log diario vacío — no hay oportunidades para resumir.")
            return None

        logger.info(f"Generando resumen de {len(opportunities)} oportunidades del {log.get('date')}")

        prompt = (
            f"Oportunidades detectadas el {log.get('date')} "
            f"({len(opportunities)} señales totales):\n\n"
            + json.dumps(opportunities, ensure_ascii=False, indent=2)
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=RANKING_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=900,
                ),
            )
            data = json.loads(response.text)
            data["date"] = log.get("date", "N/A")
            return data
        except Exception as e:
            logger.error(f"Error generando resumen rankeado: {e}")
            return None

    def clear_log(self) -> None:
        """Reinicia el log diario (llamar tras enviar el resumen)."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        DAILY_LOG_PATH.parent.mkdir(exist_ok=True)
        DAILY_LOG_PATH.write_text(
            json.dumps({"date": today, "opportunities": []}, indent=2),
            encoding="utf-8",
        )
        logger.info("Log diario reiniciado correctamente.")

    def _load_log(self) -> dict:
        if DAILY_LOG_PATH.exists():
            try:
                return json.loads(DAILY_LOG_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"date": "", "opportunities": []}
