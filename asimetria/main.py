import logging
import sys
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
logger = logging.getLogger("asimetria.main")

SEPARATOR = "=" * 60


def run_pipeline() -> None:
    logger.info(SEPARATOR)
    logger.info("INICIANDO PIPELINE: ASIMETRIA")
    logger.info(f"Ventana de busqueda : {settings.LOOKBACK_HOURS}h")
    logger.info(f"Confianza minima    : {settings.MIN_CONFIDENCE}")
    logger.info(f"Modelo LLM          : {settings.OPENAI_MODEL}")
    logger.info(SEPARATOR)

    scraper = ScrapingAgent(settings)
    analyzer = AnalysisAgent(settings)
    filter_agent = EthicalFilterAgent(settings)
    alert_agent = AlertAgent(settings)
    summary_agent = SummaryAgent(settings)

    # ─── Paso 1: Scraping ────────────────────────────────────────
    news_items = scraper.fetch_news()
    if not news_items:
        logger.info("No se encontraron noticias nuevas en la ventana configurada. Finalizando.")
        return

    # ─── Paso 2: Contexto de mercado ─────────────────────────────
    market_context = scraper.get_market_context(settings.MONITORED_TICKERS)
    tickers_ok = list(market_context.keys())
    logger.info(f"Contexto de mercado: {tickers_ok if tickers_ok else 'No disponible'}")

    # ─── Paso 3: Análisis y filtrado ─────────────────────────────
    total_analyzed = 0
    total_asymmetric = 0
    total_sent = 0

    for item in news_items:
        total_analyzed += 1
        logger.debug(f"[{total_analyzed}/{len(news_items)}] Analizando: {item.title[:70]}")

        # Análisis LLM
        result = analyzer.analyze(item, market_context)

        if not result.is_asymmetric:
            continue

        total_asymmetric += 1

        if result.confidence < settings.MIN_CONFIDENCE:
            logger.info(
                f"  Baja confianza ({result.confidence:.0%}) — descartada: {item.title[:50]}"
            )
            continue

        logger.info(
            f"  OPORTUNIDAD [{result.confidence:.0%}] {result.direction.upper()} "
            f"en {result.asset_mentioned or 'N/A'}: {item.title[:50]}"
        )

        # Filtro ético
        decision = filter_agent.passes_filter(result)
        if not decision.passes:
            logger.info(f"  Rechazada (filtro etico): {decision.reason}")
            continue

        # Enviar alerta y registrar en log diario
        sent = alert_agent.send_opportunity(result)
        if sent:
            total_sent += 1
            summary_agent.append_opportunity(result)

    # ─── Resumen final ────────────────────────────────────────────
    logger.info(SEPARATOR)
    logger.info(f"Noticias analizadas  : {total_analyzed}")
    logger.info(f"Señales asimétricas  : {total_asymmetric}")
    logger.info(f"Alertas enviadas     : {total_sent}")
    logger.info(SEPARATOR)

    if settings.SEND_SUMMARY:
        alert_agent.send_summary(total_analyzed, total_sent)


if __name__ == "__main__":
    run_pipeline()
