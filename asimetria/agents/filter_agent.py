import json
import logging
from openai import OpenAI

from agents.models import AnalysisResult, FilterDecision
from config.settings import Settings

logger = logging.getLogger(__name__)

# ---- Lista base de entidades excluidas por criterios éticos ----
BASE_BLOCKLIST = {
    # Industria armamentística israelí y afines
    "elbit systems",
    "rafael advanced defense systems",
    "israel aerospace industries",
    "iai",
    "israel weapon industries",
    "soltam systems",
    "haifa chemicals",
    # Instituciones financieras con vínculos documentados a asentamientos ilegales
    "bank hapoalim",
    "bank leumi",
    "mizrahi-tefahot bank",
    "first international bank of israel",
    # Empresas de telecomunicaciones en territorios ocupados
    "cellcom israel",
    "partner communications",
    "hot mobile",
    # Otras entidades documentadas
    "idf",
    "israel defense forces",
}

FILTER_SYSTEM_PROMPT = """Eres un auditor de cumplimiento ético para un fondo de inversión responsable.
Tu función es identificar si las entidades mencionadas en una oportunidad de inversión deben ser excluidas
según los criterios éticos del inversor.

CRITERIOS DE EXCLUSIÓN AUTOMÁTICA:
1. Contratistas de defensa con contratos activos en zonas de conflicto con población civil
2. Empresas con vínculos documentados a políticas de apartheid o colonización de territorios
3. Instituciones que financian activamente la expansión de asentamientos declarados ilegales por el derecho internacional
4. Entidades que apoyan económicamente movimientos o gobiernos involucrados en limpieza étnica documentada
5. Empresas cuyos productos son usados para vigilancia y represión de poblaciones civiles

Si la noticia NO menciona directamente ninguna entidad problemática bajo estos criterios,
la oportunidad PASA el filtro (passes_filter: true).

Responde EXCLUSIVAMENTE en JSON válido:
{
  "passes_filter": true,
  "reason": "",
  "flagged_entities": []
}"""

FILTER_USER_TEMPLATE = """Evalúa éticamente la siguiente oportunidad de inversión:

ACTIVO PRINCIPAL: {asset}
ENTIDADES MENCIONADAS: {entities}
DIRECCIÓN: {direction}
ANÁLISIS: {reasoning}
TITULAR: {title}

¿Supera los criterios éticos del inversor?"""


class EthicalFilterAgent:
    def __init__(self, settings: Settings):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.blocklist = BASE_BLOCKLIST | {e.lower() for e in settings.CUSTOM_BLOCKLIST}

    def passes_filter(self, result: AnalysisResult) -> FilterDecision:
        """
        Aplica filtro ético en dos etapas:
        1. Búsqueda rápida en lista negra (sin LLM)
        2. Evaluación semántica por LLM para casos no obvios
        """
        # Etapa 1: Búsqueda en lista negra
        combined_text = (
            result.news_item.title + " " +
            result.news_item.summary + " " +
            " ".join(result.entities)
        ).lower()

        flagged = [entity for entity in self.blocklist if entity in combined_text]

        if flagged:
            return FilterDecision(
                passes=False,
                reason=f"Entidad(es) en lista de exclusión ética: {', '.join(flagged)}",
                flagged_entities=flagged,
            )

        # Etapa 2: Evaluación LLM para entidades no catalogadas
        try:
            user_msg = FILTER_USER_TEMPLATE.format(
                asset=result.asset_mentioned or "No especificado",
                entities=", ".join(result.entities) if result.entities else "Ninguna específica",
                direction=result.direction,
                reasoning=result.reasoning,
                title=result.news_item.title,
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": FILTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=250,
            )

            data = json.loads(response.choices[0].message.content)

            return FilterDecision(
                passes=bool(data.get("passes_filter", True)),
                reason=str(data.get("reason", "")),
                flagged_entities=list(data.get("flagged_entities", [])),
            )

        except Exception as e:
            logger.error(f"Error en filtro ético LLM: {e}")
            # Fail-open: si falla la evaluación, dejamos pasar para no bloquear señales válidas
            return FilterDecision(passes=True, reason="", flagged_entities=[])
