import json
import os
import sys
from datetime import datetime
from agents.data_agent import DataAgent
from agents.analysis_agent import AnalysisAgent
from agents.selector_agent import SelectorAgent
from agents.report_agent import ReportAgent
from agents.quality_filter_agent import QualityFilterAgent
from agents.sentiment_agent import SentimentAgent
from utils.tickers_sp500 import symbols_sp500
from utils.tickers_nasdaq100 import symbols_nasdaq
from utils.tickers_stoxx50 import symbols_stoxx
from utils.tickers_dax40 import symbols_dax40
from utils.tickers_ftse100 import symbols_ftse100
from utils.tickers_russell2000 import symbols_russell2000
from utils.tickers_etfs import symbols_etfs


def main():
    # Cargar configuración
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # Determinar tipo de reporte según el día
    today = datetime.utcnow().weekday()  # 0=Lunes, 4=Viernes
    
    # Permitir override desde argumentos
    report_type = "detailed"  # Por defecto viernes
    if len(sys.argv) > 1:
        report_type = sys.argv[1]  # "detailed" o "update"
    else:
        # Auto-detectar según día
        if today == 0:  # Lunes
            report_type = "update"
        elif today == 4:  # Viernes
            report_type = "detailed"
    
    print(f"{'='*50}")
    print(f"🚀 SWING TRADING ANALYZER")
    print(f"📅 Día: {datetime.utcnow().strftime('%A, %d %B %Y')}")
    print(f"📊 Tipo de reporte: {report_type.upper()}")
    print(f"{'='*50}\n")

    # Unificar símbolos según mercados configurados
    markets_config = config.get("markets", {})
    all_symbols = []
    
    # USA
    if "sp500" in markets_config.get("usa", []):
        all_symbols.extend(symbols_sp500)
        print(f"   ├─ S&P 500: {len(symbols_sp500)} valores")
    
    if "nasdaq100" in markets_config.get("usa", []):
        all_symbols.extend(symbols_nasdaq)
        print(f"   ├─ NASDAQ 100: {len(symbols_nasdaq)} valores")
    
    if "russell2000" in markets_config.get("usa", []):
        all_symbols.extend(symbols_russell2000)
        print(f"   ├─ Russell 2000: {len(symbols_russell2000)} valores")
    
    # Europa
    if "stoxx50" in markets_config.get("europe", []):
        all_symbols.extend(symbols_stoxx)
        print(f"   ├─ STOXX 50: {len(symbols_stoxx)} valores")
    
    if "dax40" in markets_config.get("europe", []):
        all_symbols.extend(symbols_dax40)
        print(f"   ├─ DAX 40: {len(symbols_dax40)} valores")
    
    if "ftse100" in markets_config.get("europe", []):
        all_symbols.extend(symbols_ftse100)
        print(f"   ├─ FTSE 100: {len(symbols_ftse100)} valores")
    
    # ETFs
    if "sector_etfs" in markets_config.get("etfs", []):
        all_symbols.extend(symbols_etfs)
        print(f"   └─ ETFs: {len(symbols_etfs)} valores")
    
    # Eliminar duplicados
    all_symbols = list(set(all_symbols))
    print(f"\n🔍 Total único: {len(all_symbols)} símbolos")
    print()

    # PASO 1: Filtros de calidad (capitalización, volumen, spread)
    print("🔍 PASO 1/6: Aplicando filtros de calidad...")
    quality_filter = QualityFilterAgent(config)
    filtered_symbols = quality_filter.filter_symbols(all_symbols)
    
    if not filtered_symbols:
        print("⚠️ Ningún símbolo pasó los filtros de calidad. Abortando.\n")
        return
    
    print(f"✅ {len(filtered_symbols)} símbolos pasaron filtros de calidad\n")

    # PASO 2: Análisis de sentiment (noticias, earnings, insiders)
    print("📰 PASO 2/6: Analizando sentiment y contexto fundamental...")
    sentiment_agent = SentimentAgent(config)
    sentiment_filtered, sentiment_data = sentiment_agent.filter_symbols(filtered_symbols)
    
    if not sentiment_filtered:
        print("⚠️ Ningún símbolo pasó análisis de sentiment.\n")
        sentiment_filtered = filtered_symbols  # Continuar sin filtro si está deshabilitado
    
    print(f"✅ {len(sentiment_filtered)} símbolos con sentiment favorable\n")

    # PASO 3: Descargar datos históricos con todos los indicadores
    print("📥 PASO 3/6: Descargando datos históricos...")
    data_agent = DataAgent(sentiment_filtered, config)
    data = data_agent.batch_download()

    if not data:
        print("⚠️ No se pudieron descargar datos. Abortando.\n")
        return

    print(f"✅ Datos descargados: {len(data)} activos procesados\n")

    # PASO 4: Analizar con criterios ultra-estrictos
    print("🔬 PASO 4/6: Analizando oportunidades (score 8+)...")
    analysis_agent = AnalysisAgent(config)
    results = analysis_agent.analyze(data)

    # Añadir datos de sentiment a los resultados
    if sentiment_data:
        for result in results:
            symbol = result.get('symbol')
            if symbol in sentiment_data:
                result['sentiment'] = sentiment_data[symbol]

    if not results:
        print("⚠️ No hay oportunidades que cumplan los criterios.\n")
        results = []

    # PASO 5: Seleccionar los top
    print(f"\n🎯 PASO 5/6: Seleccionando mejores oportunidades...")
    selector = SelectorAgent(config)
    top_assets = selector.select_top(results)

    # PASO 6: Generar y enviar reporte
    print(f"\n📨 PASO 6/6: Generando reporte {report_type}...")
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    reporter = ReportAgent(token=token, chat_id=chat_id, report_type=report_type)
    report = reporter.send_report(top_assets)

    # Guardar resultado localmente
    filename = f"report_{report_type}_{datetime.utcnow().strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"✅ PROCESO COMPLETADO")
    print(f"   📊 Símbolos iniciales: {len(all_symbols)}")
    print(f"   🔍 Post-filtros calidad: {len(filtered_symbols)}")
    print(f"   📰 Post-sentiment: {len(sentiment_filtered)}")
    print(f"   📥 Datos descargados: {len(data)}")
    print(f"   🎯 Oportunidades detectadas: {len(results)}")
    print(f"   ⭐ Top seleccionados: {len(top_assets)}")
    print(f"   💾 Guardado en: {filename}")
    if top_assets:
        avg_score = sum(a.get("score", 0) for a in top_assets) / len(top_assets)
        print(f"   📈 Score promedio: {avg_score:.2f}/10")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
