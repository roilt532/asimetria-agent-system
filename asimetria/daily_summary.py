"""
daily_summary.py
----------------
Script independiente que lee el log diario acumulado, genera un ranking
de oportunidades usando GPT-4o-mini y envía el resumen a Telegram.

Ejecutado automáticamente por .github/workflows/daily_summary.yml
También puede lanzarse manualmente:  python daily_summary.py
"""
import logging
import sys

from config.settings import settings
from agents.summary_agent import SummaryAgent
from agents.alert_agent import AlertAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("asimetria.daily_summary")

SEPARATOR = "=" * 60


def run_daily_summary() -> None:
    logger.info(SEPARATOR)
    logger.info("RESUMEN DIARIO ASIMETRIA — INICIO")
    logger.info(SEPARATOR)

    summary_agent = SummaryAgent(settings)
    alert_agent = AlertAgent(settings)

    # Generar ranking y resumen con GPT-4o-mini
    summary = summary_agent.generate_ranked_summary()

    if summary is None:
        logger.info("No hay oportunidades acumuladas hoy. No se envía resumen.")
        return

    ranked = summary.get("ranked_opportunities", [])
    total = summary.get("total_signals", 0)
    sentiment = summary.get("market_sentiment", "neutral")

    logger.info(f"Fecha              : {summary.get('date')}")
    logger.info(f"Señales totales    : {total}")
    logger.info(f"Sentimiento        : {sentiment}")
    logger.info(f"Activos rankeados  : {len(ranked)}")

    for opp in ranked:
        logger.info(
            f"  #{opp['rank']} {opp['asset']} | "
            f"{opp.get('direction','?').upper()} | "
            f"{int(opp.get('avg_confidence',0)*100)}% | "
            f"{opp.get('signal_count',1)} señal(es)"
        )

    # Enviar a Telegram
    sent = alert_agent.send_daily_summary(summary)
    if sent:
        logger.info("Resumen diario enviado a Telegram correctamente.")
    else:
        logger.error("Fallo al enviar el resumen diario a Telegram.")

    # Limpiar el log para el siguiente día
    summary_agent.clear_log()

    logger.info(SEPARATOR)
    logger.info("RESUMEN DIARIO ASIMETRIA — COMPLETADO")
    logger.info(SEPARATOR)


if __name__ == "__main__":
    run_daily_summary()
