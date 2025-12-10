# 📊 Analizador Financiero - Swing Trading

Sistema automatizado de análisis técnico para swing trading de acciones (3-5 días).

## 🎯 Características

- ✅ **~480 valores analizados**: S&P500, NASDAQ100, Russell 2000, STOXX50, DAX40, FTSE100, ETFs
- ✅ **Filtros de calidad**: Capitalización, volumen, liquidez, spread
- ✅ **Análisis de sentiment**: Noticias, earnings calendar, insider trading (Finnhub)
- ✅ **10 indicadores técnicos**: RSI, MACD, Stochastic, EMAs, ATR, ADX, Keltner, SuperTrend, VWAP
- ✅ **Score 8+/10**: Solo señales de alta calidad
- ✅ **Reportes automáticos**: Telegram con niveles de entrada/salida

## 📈 Indicadores Técnicos

### Osciladores
- **RSI(9)**: Detecta sobreventa/sobrecompra
- **Stochastic(9,3,3)**: Confirma momentum
- **MACD(5,13,5)**: Cruces de tendencia

### Tendencia
- **EMAs**: 5, 20, 50 períodos
- **Keltner Channels**: Soporte/resistencia dinámicos
- **SuperTrend**: Stop loss inteligente

### Volatilidad y Volumen
- **ATR(7)**: Volatilidad para stop loss
- **ADX(14)**: Fuerza de tendencia
- **VWAP**: Precio promedio ponderado por volumen

## 🚀 Deployment en Render.com

### Prerrequisitos

1. Cuenta en [Render.com](https://render.com) (gratis)
2. Repositorio en GitHub
3. Tokens de APIs:
   - Telegram Bot Token ([BotFather](https://t.me/botfather))
   - Telegram Chat ID ([userinfobot](https://t.me/userinfobot))
   - Finnhub API Key ([finnhub.io](https://finnhub.io))

### Setup

1. **Fork/Clone este repositorio**

2. **Conectar a Render:**
   - Dashboard → New → Web Service
   - Conectar repositorio GitHub
   - Configuración:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python scheduler.py`
     - **Plan**: Free

3. **Configurar variables de entorno:**
   ```
   TELEGRAM_TOKEN=tu_bot_token
   TELEGRAM_CHAT_ID=tu_chat_id
   FINNHUB_API_KEY=tu_finnhub_key
   ```

4. **Deploy** → ¡Automático! ✅

### Actualizar código

```bash
git add .
git commit -m "Update analysis logic"
git push origin main
# Render autodeploya en ~2 minutos
```

## 📅 Schedule de Ejecución

- **Lunes-Viernes 09:00 UTC**: Análisis diario con envío condicional
- **Viernes 18:00 UTC**: Informe semanal detallado (siempre se envía)

### Lógica de envío

El sistema solo envía reportes cuando:
- ✅ Encuentra oportunidades con score 8+/10
- ✅ Es viernes (informe semanal)

Si no hay oportunidades → No envía spam → Reintenta al día siguiente.

## 🔧 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/analizador_financiero.git
cd analizador_financiero

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export TELEGRAM_TOKEN="tu_token"
export TELEGRAM_CHAT_ID="tu_chat_id"
export FINNHUB_API_KEY="tu_finnhub_key"

# Ejecutar análisis manual
python orchestrator.py

# O ejecutar scheduler
python scheduler.py
```

## 📁 Estructura del Proyecto

```
analizador_financiero/
├── agents/                      # Agentes especializados
│   ├── data_agent.py           # Descarga y cálculo de indicadores
│   ├── analysis_agent.py       # Sistema de scoring
│   ├── selector_agent.py       # Filtros finales
│   ├── report_agent.py         # Generación de reportes
│   ├── quality_filter_agent.py # Filtros de calidad
│   └── sentiment_agent.py      # Análisis de sentiment
├── utils/                       # Listas de tickers
│   ├── tickers_sp500.py
│   ├── tickers_nasdaq100.py
│   ├── tickers_russell2000.py
│   ├── tickers_stoxx50.py
│   ├── tickers_dax40.py
│   ├── tickers_ftse100.py
│   └── tickers_etfs.py
├── docs/                        # Documentación
│   ├── FINNHUB_SETUP.md
│   └── RENDER_SETUP.md
├── orchestrator.py              # Coordinador principal
├── scheduler.py                 # Programador de tareas
├── config.json                  # Configuración
├── requirements.txt             # Dependencias
├── render.yaml                  # Config de Render
├── .gitignore
└── README.md
```

## ⚙️ Configuración

Editar `config.json` para ajustar:

```json
{
  "scoring": {
    "green_threshold": 8.5,  // Score mínimo para señal fuerte
    "yellow_threshold": 8.0   // Score mínimo aceptable
  },
  "targets": {
    "profit_target_pct": 7.0,  // Objetivo de ganancia
    "stop_loss_pct": 1.0        // Stop loss
  },
  "quality_filters": {
    "min_market_cap": 5000000000,  // Cap mínima $5B
    "min_avg_volume": 1000000       // Volumen mínimo
  }
}
```

## 🧪 Testing

```bash
# Test de conexión Finnhub
python test_finnhub.py

# Test de sistema completo
python orchestrator.py
```

## 📊 Ejemplo de Reporte

```
📊 OPORTUNIDADES DETECTADAS - MARTES
🕐 12/11/2024 09:00 UTC
════════════════════════════════════

🟢 1. AAPL - Score: 8.7/10
   📍 Rebote alcista confirmado (MUY FUERTE)
   💰 Precio actual: $178.50
   🎯 Objetivo (+7%): $191.00
   🛡️ Stop Loss: $176.72 (-1.0%)
   📊 RSI: 24 | Stoch: 18
   📈 Sentiment: 0.45 | Noticias: 10
   💼 Insiders: bullish
```

## ⚠️ Importante

### Este repositorio NO usa GitHub Actions

El código se almacena en GitHub únicamente como repositorio.
La ejecución se realiza en **Render.com**.

### Compliance

- ✅ Cumple términos de GitHub
- ✅ No usa infraestructura de GitHub para computación
- ✅ Solo version control y colaboración

## 📚 Documentación Adicional

- [Setup de Finnhub API](docs/FINNHUB_SETUP.md)
- [Deploy en Render.com](docs/RENDER_SETUP.md)

## 💰 Costos

- **GitHub**: Gratis (solo repositorio)
- **Render.com**: Gratis (750h/mes)
- **Finnhub API**: Gratis (60 req/min)
- **Telegram Bot**: Gratis
- **Yahoo Finance**: Gratis

**Total: $0/mes** ✅

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit (`git commit -m 'Add mejora'`)
4. Push (`git push origin feature/mejora`)
5. Abre un Pull Request

## 📜 Licencia

MIT License - Ver [LICENSE](LICENSE)

## 📧 Soporte

Para issues o preguntas:
- GitHub Issues: [github.com/tu-usuario/analizador_financiero/issues](https://github.com)
- Documentación: Ver carpeta `docs/`

---

**⚠️ Disclaimer**: Este sistema es una herramienta de análisis técnico. No constituye asesoramiento financiero. Invierte bajo tu propia responsabilidad.
