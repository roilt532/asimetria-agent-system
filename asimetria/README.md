# Asimetría — Sistema Multi-Agente de Detección de Oportunidades Financieras

Sistema autónomo de scraping, análisis con IA (Gemini 2.5 Pro) y filtrado ético de noticias financieras y crypto. Se ejecuta automáticamente en GitHub Actions y te envía alertas y un resumen diario por Telegram.

---

## Estructura del Proyecto

```
asimetria/
├── .github/
│   └── workflows/
│       ├── daily_digest.yml    # Digest diario a las 07:30 UTC (PRINCIPAL)
│       └── main.yml            # Alertas en tiempo real cada 2 horas (OPCIONAL)
├── agents/
│   ├── models.py               # Dataclasses: NewsItem, AnalysisResult, FilterDecision
│   ├── scraping_agent.py       # 9 feeds RSS + yfinance (sin API key)
│   ├── analysis_agent.py       # Gemini: ¿es una señal asimétrica?
│   ├── filter_agent.py         # Filtro ético (lista negra + LLM)
│   ├── alert_agent.py          # Envío a Telegram Bot API
│   └── summary_agent.py        # Ranking y resumen consolidado
├── config/
│   └── settings.py             # Variables de entorno
├── main.py                     # Pipeline de alertas en tiempo real
├── daily_digest.py             # Script del digest diario (autocontenido)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Cómo funciona (flujo)

```
                    ┌─ daily_digest.py (1x día, 07:30 UTC) ─────────────────────┐
                    │                                                             │
  RSS Feeds (9) ────┤  ScrapingAgent (24h)                                      │
  yfinance (BTC..)  │       │                                                    │
                    │       ▼                                                    │
                    │  AnalysisAgent (Gemini 2.5 Pro)                           │
                    │  ¿Es señal asimétrica? confidence >= 0.65?                │
                    │       │ Sí                                                 │
                    │       ▼                                                    │
                    │  EthicalFilterAgent (lista negra + LLM)                   │
                    │       │ Pasa                                               │
                    │       ▼                                                    │
                    │  SummaryAgent → Ranking Gemini → 1 mensaje Telegram       │
                    └────────────────────────────────────────────────────────────┘

                    ┌─ main.py (8x día, cada 2h) ─────────┐
                    │  Igual que arriba pero:               │
                    │  - Ventana: últimas 3 horas           │
                    │  - Alerta individual por señal         │
                    │  - confidence >= 0.75                  │
                    └──────────────────────────────────────┘
```

---

## Setup en GitHub (paso a paso)

### Paso 1 — Subir el código a GitHub

```bash
git init
git add .
git commit -m "feat: sistema asimetria"
git remote add origin https://github.com/TU_USUARIO/asimetria.git
git push -u origin main
```

### Paso 2 — Añadir los 3 Secrets obligatorios

En tu repositorio → **Settings → Secrets and variables → Actions → Secrets → New repository secret**

| Secret | Valor | Dónde obtenerlo |
|--------|-------|-----------------|
| `GEMINI_API_KEY` | `AIzaSy...` | https://aistudio.google.com/apikey (gratis) |
| `TELEGRAM_BOT_TOKEN` | `123456:AABBcc...` | @BotFather en Telegram → /newbot |
| `TELEGRAM_CHAT_ID` | `123456789` | @userinfobot en Telegram |

### Paso 3 — Activar los workflows

- Ve a **Actions** en tu repositorio
- Si aparece un banner "Workflows disabled", haz clic en **"Enable workflows"**
- Listo. El digest se enviará cada día a las 07:30 UTC (09:30 España)

### Paso 4 — Probar manualmente (recomendado)

Antes de esperar al primer cron, prueba que todo funciona:
1. Ve a **Actions → Asimetria — Digest Diario**
2. Clic en **"Run workflow"** → **"Run workflow"**
3. Espera 3-5 minutos
4. Comprueba que llega el mensaje a Telegram

---

## Obtener las API Keys

### GEMINI_API_KEY (Google AI Studio — GRATIS)
1. Ve a https://aistudio.google.com/apikey
2. Inicia sesión con tu cuenta Google
3. Clic en **"Create API key"**
4. Copia la key (empieza con `AIza...`)
5. Pégala como Secret `GEMINI_API_KEY` en GitHub

### TELEGRAM_BOT_TOKEN
1. Abre Telegram → busca **@BotFather**
2. Envía `/newbot` y sigue las instrucciones
3. Elige un nombre y username para tu bot
4. BotFather te dará: `123456789:AABBCCDDEEFFaabbcc...`
5. Pégalo como Secret `TELEGRAM_BOT_TOKEN`

### TELEGRAM_CHAT_ID
1. Busca **@userinfobot** en Telegram
2. Envía cualquier mensaje
3. Te responde con tu ID (un número como `123456789`)
4. Pégalo como Secret `TELEGRAM_CHAT_ID`
> Si quieres enviar a un grupo: añade el bot al grupo, envía un mensaje mencionándolo,
> y usa `https://api.telegram.org/bot<TOKEN>/getUpdates` para ver el chat_id del grupo (será negativo).

---

## Configuración avanzada (Variables opcionales)

En **Settings → Secrets and variables → Actions → Variables**:

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `GEMINI_MODEL` | `gemini-2.5-pro` | Modelo de Gemini a usar |
| `MIN_CONFIDENCE` | `0.75` | Umbral alertas en tiempo real |
| `CUSTOM_BLOCKLIST` | _(vacío)_ | Entidades extra a excluir (separadas por comas) |

---

## Ejecución local

```bash
cp .env.example .env
# Edita .env con tus keys reales
pip install -r requirements.txt

# Digest diario (24h de noticias):
python daily_digest.py

# Pipeline de alertas en tiempo real:
python main.py
```

---

## Fuentes de datos (sin API key)

| Fuente | Contenido |
|--------|-----------|
| Yahoo Finance | Top noticias financieras + Bitcoin |
| CoinDesk | Noticias crypto |
| CoinTelegraph | Análisis crypto |
| Bitcoinist | Noticias Bitcoin |
| CryptoNews | Mercado crypto |
| Reuters Business | Noticias financieras globales |
| CNBC Markets | Mercados y economía |
| MarketWatch | Análisis de mercados |
| yfinance | Precios en tiempo real (BTC, ETH, SPY, QQQ, GLD) |

---

## Personalización

### Cambiar horario del digest
Edita `.github/workflows/daily_digest.yml`:
```yaml
- cron: '30 7 * * *'   # 07:30 UTC — actual
- cron: '0 6 * * *'    # 06:00 UTC
- cron: '0 17 * * *'   # 17:00 UTC (antes del cierre de NY)
```

### Añadir entidades a la lista negra
En `.env` o como Variable en GitHub Actions:
```
CUSTOM_BLOCKLIST=empresa1,empresa2,entidad3
```
