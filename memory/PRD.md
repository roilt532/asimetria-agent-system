# PRD — Sistema Asimetría

## Descripción
Sistema multi-agente autónomo de detección de oportunidades de inversión asimétricas
en mercados financieros y criptomonedas, con filtro ético integrado y alertas por Telegram.

## Fecha: Febrero 2026

## Arquitectura

```
RSS Feeds (9 fuentes) + yfinance → ScrapingAgent → AnalysisAgent (GPT-4o-mini)
→ EthicalFilterAgent (blocklist + LLM) → AlertAgent (Telegram Bot API)
```

## Stack Tecnológico
- Python 3.11+
- openai >= 1.30.0 (GPT-4o-mini)
- yfinance >= 0.2.40
- feedparser >= 6.0.11
- python-dotenv >= 1.0.0
- requests >= 2.31.0
- python-dateutil >= 2.9.0

## Estructura del Proyecto
```
asimetria/
├── .github/workflows/main.yml   # GitHub Actions cron (cada 30 min)
├── agents/
│   ├── models.py                # NewsItem, AnalysisResult, FilterDecision
│   ├── scraping_agent.py        # 9 feeds RSS + yfinance
│   ├── analysis_agent.py        # Análisis LLM asimétrico
│   ├── filter_agent.py          # Filtro ético (blocklist + LLM)
│   └── alert_agent.py           # Telegram Bot API
├── config/settings.py           # Variables de entorno
├── main.py                      # Orquestador del pipeline
├── requirements.txt
├── .env.example                 # Plantilla credenciales
└── README.md
```

## Implementado
- [x] ScrapingAgent: 9 fuentes RSS financieras/crypto gratuitas + yfinance
- [x] AnalysisAgent: GPT-4o-mini con JSON mode para detección de señales asimétricas
- [x] EthicalFilterAgent: Stage 1 (blocklist hardcoded) + Stage 2 (evaluación LLM)
- [x] AlertAgent: Telegram Bot API con mensajes HTML formateados + send_daily_summary()
- [x] SummaryAgent: Ranking diario consolidado (append + generate_ranked_summary + clear_log)
- [x] main.py: Pipeline orquestado con logging detallado + integración SummaryAgent
- [x] daily_summary.py: Script independiente para el resumen diario
- [x] GitHub Actions main.yml: Cron cada 30 min + cache para persistir log diario
- [x] GitHub Actions daily_summary.yml: Cron diario 20:00 UTC (22:00 España)
- [x] .env.example + README con guía de setup completa
- [x] Validación: 17 archivos, 908 líneas, sintaxis OK, RSS live OK, yfinance live OK, tests de lógica OK

## Variables de Entorno Requeridas
- OPENAI_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

## Variables Opcionales
- OPENAI_MODEL (default: gpt-4o-mini)
- MIN_CONFIDENCE (default: 0.75)
- LOOKBACK_HOURS (default: 2)
- SEND_SUMMARY (default: false)
- CUSTOM_BLOCKLIST (default: vacío)

## Backlog / Mejoras Futuras
- P1: Persistencia de URLs procesadas (evitar duplicados entre runs)
- P1: Dashboard web ligero con historial de alertas
- P2: Soporte multi-usuario (múltiples Telegram chat_ids)
- P2: Webhook de Discord como canal alternativo
- P2: Análisis de sentimiento adicional con CryptoPanic API
- P3: Backtesting del sistema con noticias históricas
