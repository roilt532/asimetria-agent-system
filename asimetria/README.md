# Asimetría — Sistema Multi-Agente de Detección de Oportunidades Financieras

Sistema autónomo de scraping, análisis con IA y filtrado ético de noticias financieras y crypto.
Ejecuta cada 30 minutos vía GitHub Actions y envía alertas a Telegram solo con las mejores señales.

---

## Estructura del Proyecto

```
asimetria/
├── .github/
│   └── workflows/
│       └── main.yml          # Cron job automático (GitHub Actions)
├── agents/
│   ├── __init__.py
│   ├── models.py             # Dataclasses: NewsItem, AnalysisResult, FilterDecision
│   ├── scraping_agent.py     # RSS feeds + yfinance (sin API key)
│   ├── analysis_agent.py     # GPT-4o-mini: ¿es una señal asimétrica?
│   ├── filter_agent.py       # Filtro ético (lista negra + LLM)
│   └── alert_agent.py        # Envío de alertas vía Telegram Bot API
├── config/
│   ├── __init__.py
│   └── settings.py           # Carga variables de entorno
├── main.py                   # Orquestador principal del pipeline
├── requirements.txt
├── .env.example              # Plantilla de variables de entorno
└── README.md
```

---

## Flujo del Pipeline

```
RSS Feeds (9 fuentes) ──┐
                         ├──► ScrapingAgent ──► [NewsItem list]
yfinance (BTC, ETH...) ─┘
                                     │
                                     ▼
                              AnalysisAgent (GPT-4o-mini)
                          ¿Es una señal asimétrica temprana?
                              confidence >= MIN_CONFIDENCE?
                                     │ Sí
                                     ▼
                           EthicalFilterAgent
                        (lista negra + evaluación LLM)
                                     │ Pasa
                                     ▼
                             AlertAgent → Telegram
```

---

## Configuración Rápida

### 1. Clonar y preparar entorno

```bash
git clone https://github.com/TU_USUARIO/asimetria.git
cd asimetria
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales reales (ver sección "Obtener API Keys" abajo).

### 3. Ejecutar localmente

```bash
python main.py
```

---

## Obtener las API Keys

### OpenAI API Key
1. Regístrate en [https://platform.openai.com](https://platform.openai.com)
2. Ve a **API Keys** → **Create new secret key**
3. Copia la key (empieza con `sk-...`) y pégala en `OPENAI_API_KEY`
4. Asegúrate de tener créditos disponibles en tu cuenta

### Telegram Bot Token
1. Abre Telegram y busca **@BotFather**
2. Envía el comando `/newbot`
3. Sigue las instrucciones: elige nombre y username para tu bot
4. BotFather te dará un token como `123456789:AABBCCDDEEFFaabbccddeeff`
5. Pégalo en `TELEGRAM_BOT_TOKEN`

### Telegram Chat ID
1. Busca **@userinfobot** en Telegram y envía cualquier mensaje
2. Te responderá con tu Chat ID (número)
3. Alternativamente: inicia una conversación con tu bot y visita:
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
4. Copia el valor de `"id"` dentro de `"chat"` y pégalo en `TELEGRAM_CHAT_ID`

---

## Despliegue en GitHub Actions

### Paso 1: Subir el repositorio a GitHub

```bash
git init
git add .
git commit -m "feat: sistema asimetria inicial"
git remote add origin https://github.com/TU_USUARIO/asimetria.git
git push -u origin main
```

### Paso 2: Configurar Secrets en GitHub

En tu repositorio → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Valor |
|--------|-------|
| `OPENAI_API_KEY` | Tu key de OpenAI |
| `TELEGRAM_BOT_TOKEN` | Token de tu bot de Telegram |
| `TELEGRAM_CHAT_ID` | Tu Chat ID de Telegram |

### Paso 3: Configurar Variables (opcionales)

En la misma sección, pestaña **Variables**:

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `MIN_CONFIDENCE` | `0.75` | Umbral mínimo de confianza (0.0–1.0) |
| `LOOKBACK_HOURS` | `2` | Horas hacia atrás para buscar noticias |
| `SEND_SUMMARY` | `false` | Enviar resumen al final de cada run |
| `CUSTOM_BLOCKLIST` | _(vacío)_ | Entidades extra a excluir (separadas por comas) |

### Paso 4: Activar el workflow

El workflow se activa automáticamente cada 30 minutos.
También puedes ejecutarlo manualmente desde **Actions** → **Asimetria Pipeline** → **Run workflow**.

---

## Fuentes de Datos (sin API key)

| Fuente | Tipo | Contenido |
|--------|------|-----------|
| Yahoo Finance | RSS | Top noticias financieras |
| Yahoo Finance BTC | RSS | Noticias específicas de Bitcoin |
| CoinDesk | RSS | Noticias de criptomonedas |
| CoinTelegraph | RSS | Análisis y noticias crypto |
| Bitcoinist | RSS | Noticias y análisis Bitcoin |
| CryptoNews | RSS | Noticias del mercado crypto |
| Reuters Business | RSS | Noticias financieras globales |
| CNBC Markets | RSS | Mercados y economía |
| MarketWatch | RSS | Análisis de mercados |
| yfinance | Python lib | Precios en tiempo real (BTC, ETH, SPY, QQQ, GLD) |

---

## Personalización

### Añadir más tickers monitoreados
Edita `MONITORED_TICKERS` en `config/settings.py`:
```python
MONITORED_TICKERS: list = ["BTC-USD", "ETH-USD", "SOL-USD", "AAPL", "TSLA"]
```

### Añadir entidades a la lista de exclusión ética
En tu `.env`:
```
CUSTOM_BLOCKLIST=empresa1,empresa2,entidad3
```

### Cambiar la frecuencia del cron
Edita `.github/workflows/main.yml`:
```yaml
- cron: '*/15 * * * *'   # Cada 15 minutos
- cron: '0 * * * *'      # Cada hora
- cron: '0 9,21 * * *'   # A las 9:00 y 21:00 UTC
```

---

## Requisitos

- Python 3.11+
- Cuenta OpenAI con créditos disponibles
- Bot de Telegram creado vía @BotFather
