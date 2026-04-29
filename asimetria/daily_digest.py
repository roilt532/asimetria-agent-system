"""
daily_digest.py
---------------
Script autocontenido para el resumen diario de Asimetría.

En una sola ejecución:
  1. Obtiene TODAS las noticias de las últimas 24h (9 feeds RSS + yfinance)
  2. Analiza cada noticia con Gemini para detectar oportunidades asimétricas
  3. Aplica el filtro ético
  4. Rankea las mejores oportunidades
  5. Envía UN único mensaje de resumen consolidado a Telegram

No depende de estado externo ni de cache entre runs.
Se ejecuta una vez al día via .github/workflows/daily_digest.yml
También puede lanzarse manualmente: python daily_digest.py
"""
import os
import logging
import sys

# Forzar ventana de 24h ANTES de que Settings se inicialice.
# setdefault respeta si LOOKBACK_HOURS ya está en el entorno (ej. si el workflow lo sobreescribe).
os.environ.setdefault("LOOKBACK_HOURS", "24")
# Umbral de confianza un poco más bajo para el digest diario
# (queremos más señales para rankear, no solo las de altísima confianza)
os.environ.setdefault("MIN_CONFIDENCE", "0.65")

from config.settings import settings
from agents.scraping_agent import ScrapingAgent
from agents.analysis_agent import AnalysisAgent
from agents.filter_agent import EthicalFilterAgent
from agents.alert_agent import AlertAgent
from agents.summary_agent import SummaryAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("asimetria.daily_digest")

SEPARATOR = "=" * 60


def run_daily_digest() -> None:
    logger.info(SEPARATOR)
    logger.info("DIGEST DIARIO ASIMETRIA — INICIO")
    logger.info(f"Ventana de análisis : {settings.LOOKBACK_HOURS}h")
    logger.info(f"Confianza mínima    : {settings.MIN_CONFIDENCE}")
    logger.info(f"Modelo LLM          : {settings.GEMINI_MODEL}")
    logger.info(SEPARATOR)

    scraper = ScrapingAgent(settings)
    analyzer = AnalysisAgent(settings)
    filter_agent = EthicalFilterAgent(settings)
    alert_agent = AlertAgent(settings)
    summary_agent = SummaryAgent(settings)

    # ─── Paso 1: Scraping de las últimas 24h ─────────────────────
    news_items = scraper.fetch_news()
    logger.info(f"Noticias encontradas (24h): {len(news_items)}")

    if not news_items:
        logger.info("Sin noticias disponibles. Finalizando sin enviar resumen.")
        return

    # ─── Paso 2: Contexto de mercado ─────────────────────────────
    market_context = scraper.get_market_context(settings.MONITORED_TICKERS)
    logger.info(f"Contexto de mercado : {list(market_context.keys())}")

    # ─── Paso 3: Analizar cada noticia y filtrar ──────────────────
    total_analyzed = 0
    total_opportunities = 0

    for item in news_items:
        total_analyzed += 1

        result = analyzer.analyze(item, market_context)

        if not result.is_asymmetric or result.confidence < settings.MIN_CONFIDENCE:
            continue

        decision = filter_agent.passes_filter(result)
        if not decision.passes:
            logger.info(f"  [FILTRADO] {decision.reason[:80]}")
            continue

        # Guardar en log temporal (en memoria del mismo run)
        summary_agent.append_opportunity(result)
        total_opportunities += 1
        logger.info(
            f"  [{result.confidence:.0%}] {result.direction.upper()} "
            f"{result.asset_mentioned or 'N/A'} — {item.title[:55]}"
        )

    logger.info(SEPARATOR)
    logger.info(f"Noticias analizadas   : {total_analyzed}")
    logger.info(f"Oportunidades válidas : {total_opportunities}")
    logger.info(SEPARATOR)

    if total_opportunities == 0:
        logger.info("Sin oportunidades asimétricas hoy. No se envía resumen.")
        # Enviar igualmente un mensaje de "sin señales" para confirmar que el sistema funciona
        alert_agent._send(
            "<b>DIGEST DIARIO — ASIMETRIA</b>\n\n"
            "Sin oportunidades asimétricas detectadas hoy.\n"
            "El sistema está funcionando correctamente.\n\n"
            "<i>Sistema Asimetria — Generado automáticamente</i>"
        )
        return

    # ─── Paso 4: Generar ranking con Gemini ──────────────────────
    logger.info("Generando ranking con Gemini...")
    summary = summary_agent.generate_ranked_summary()

    if summary is None:
        logger.error("Error generando el ranking. No se envía resumen.")
        return

    # ─── Paso 5: Enviar a Telegram ────────────────────────────────
    sent = alert_agent.send_daily_summary(summary)
    if sent:
        logger.info("Digest diario enviado a Telegram correctamente.")
    else:
        logger.error("Error al enviar el digest a Telegram.")

    # ─── Limpieza del log temporal ────────────────────────────────
    summary_agent.clear_log()

    logger.info(SEPARATOR)
    logger.info("DIGEST DIARIO ASIMETRIA — COMPLETADO")
    logger.info(SEPARATOR)


if __name__ == "__main__":
    run_daily_digest()
