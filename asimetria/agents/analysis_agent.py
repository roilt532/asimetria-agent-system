import json
import logging
from google import genai
from google.genai import types

from agents.models import NewsItem, AnalysisResult
from config.settings import Settings

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """Eres un analista de inversiones especializado en detectar OPORTUNIDADES ASIMÉTRICAS.
Tu objetivo: identificar noticias que representen una señal temprana ANTES de que se vuelvan virales o mainstream.

Una "oportunidad asimétrica" válida cumple TODOS estos criterios:
1. La noticia es reciente y aún no está en todos los grandes medios
2. Tiene impacto directo y cuantificable en un activo financiero (cripto, acción, commodity, índice)
3. El potencial de movimiento de precio supera significativamente el riesgo conocido
4. Es objetiva y basada en hechos concretos (no especulación ni opinión)

Responde EXCLUSIVAMENTE en JSON válido con esta estructura exacta:
{
  "is_asymmetric": true,
  "confidence": 0.82,
  "direction": "bullish",
  "reasoning": "Descripción concisa en español del por qué es una señal asimétrica (máx 200 chars)",
  "entities": ["Empresa A", "Entidad B"],
  "asset_mentioned": "BTC"
}

Valores permitidos para direction: "bullish", "bearish", "neutral"
Si no hay oportunidad clara, devuelve is_asymmetric: false y confidence: 0.0"""

ANALYSIS_USER_TEMPLATE = """Analiza la siguiente noticia financiera y determina si representa una oportunidad asimétrica temprana.

TÍTULO: {title}
FUENTE: {source}
RESUMEN: {summary}

CONTEXTO DE MERCADO ACTUAL:
{market_context}

¿Es una oportunidad asimétrica?"""


class AnalysisAgent:
    def __init__(self, settings: Settings):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def analyze(self, item: NewsItem, market_context: dict = None) -> AnalysisResult:
        """Analiza una noticia y determina si es una oportunidad asimétrica."""
        context_str = (
            json.dumps(market_context, ensure_ascii=False, indent=2)
            if market_context
            else "No disponible"
        )

        user_msg = ANALYSIS_USER_TEMPLATE.format(
            title=item.title,
            source=item.source,
            summary=item.summary[:800],
            market_context=context_str,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=ANALYSIS_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=400,
                ),
            )

            data = json.loads(response.text)

            return AnalysisResult(
                news_item=item,
                is_asymmetric=bool(data.get("is_asymmetric", False)),
                confidence=float(data.get("confidence", 0.0)),
                direction=str(data.get("direction", "neutral")),
                reasoning=str(data.get("reasoning", ""))[:300],
                entities=list(data.get("entities", [])),
                asset_mentioned=str(data.get("asset_mentioned", "")),
            )

        except Exception as e:
            logger.error(f"Error analizando '{item.title[:60]}': {e}")
            return AnalysisResult(
                news_item=item,
                is_asymmetric=False,
                confidence=0.0,
                direction="neutral",
                reasoning=f"Error: {str(e)[:100]}",
                entities=[],
                asset_mentioned="",
            )
