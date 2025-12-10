import yfinance as yf
import time

class QualityFilterAgent:
    """
    Filtra valores según criterios de calidad fundamental.
    Elimina penny stocks, valores ilíquidos y empresas de baja calidad.
    """
    
    def __init__(self, config):
        self.config = config
        self.filters = config.get("quality_filters", {})
        self.enabled = self.filters.get("enabled", True)
    
    def get_stock_info(self, symbol):
        """Obtiene información fundamental del símbolo."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "market_cap": info.get('marketCap', 0),
                "avg_volume": info.get('averageVolume', 0),
                "current_price": info.get('currentPrice') or info.get('regularMarketPrice', 0),
                "bid": info.get('bid', 0),
                "ask": info.get('ask', 0),
                "beta": info.get('beta', 1.0),
                "short_name": info.get('shortName', symbol)
            }
        except Exception as e:
            print(f"   ⚠️ Error obteniendo info de {symbol}: {e}")
            return None
    
    def calculate_spread(self, bid, ask):
        """Calcula el spread bid-ask en porcentaje."""
        if bid > 0 and ask > 0:
            return ((ask - bid) / bid) * 100
        return 0
    
    def passes_quality_filters(self, stock_info):
        """Verifica si un valor pasa todos los filtros de calidad."""
        if not stock_info:
            return False, "No se pudo obtener información"
        
        symbol = stock_info["symbol"]
        
        # Filtro 1: Capitalización mínima
        min_cap = self.filters.get("min_market_cap", 5_000_000_000)
        market_cap = stock_info.get("market_cap", 0)
        if market_cap < min_cap:
            return False, f"Cap: ${market_cap/1e9:.1f}B < ${min_cap/1e9:.1f}B"
        
        # Filtro 2: Volumen mínimo
        min_vol = self.filters.get("min_avg_volume", 1_000_000)
        avg_volume = stock_info.get("avg_volume", 0)
        if avg_volume < min_vol:
            return False, f"Vol: {avg_volume:,} < {min_vol:,}"
        
        # Filtro 3: Precio en rango válido
        price = stock_info.get("current_price", 0)
        min_price = self.filters.get("min_price", 20.0)
        max_price = self.filters.get("max_price", 1000.0)
        if price < min_price or price > max_price:
            return False, f"Precio ${price:.2f} fuera de rango [${min_price}-${max_price}]"
        
        # Filtro 4: Spread bid-ask
        bid = stock_info.get("bid", 0)
        ask = stock_info.get("ask", 0)
        if bid > 0 and ask > 0:
            spread = self.calculate_spread(bid, ask)
            max_spread = self.filters.get("max_spread_pct", 0.5)
            if spread > max_spread:
                return False, f"Spread {spread:.2f}% > {max_spread}%"
        
        # Filtro 5: Beta (volatilidad vs mercado)
        max_beta = self.filters.get("max_beta", 1.8)
        beta = stock_info.get("beta", 1.0)
        if beta and beta > max_beta:
            return False, f"Beta {beta:.2f} > {max_beta}"
        
        # Filtro 6: Volumen en dólares
        min_volume_dollars = self.filters.get("min_volume_dollars", 20_000_000)
        volume_dollars = avg_volume * price
        if volume_dollars < min_volume_dollars:
            return False, f"Vol $: ${volume_dollars/1e6:.1f}M < ${min_volume_dollars/1e6:.1f}M"
        
        return True, "OK"
    
    def filter_symbols(self, symbols):
        """
        Filtra lista de símbolos según criterios de calidad.
        Retorna solo símbolos que pasan todos los filtros.
        """
        if not self.enabled:
            print("ℹ️  Filtros de calidad deshabilitados")
            return symbols
        
        print(f"\n🔍 FASE: FILTROS DE CALIDAD")
        print(f"{'='*50}")
        print(f"Analizando {len(symbols)} símbolos...")
        
        approved = []
        rejected = {}
        batch_size = 100  # Procesar en lotes para no saturar
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(symbols) + batch_size - 1) // batch_size
            
            print(f"\n📦 Lote {batch_num}/{total_batches} ({len(batch)} símbolos)")
            
            for symbol in batch:
                stock_info = self.get_stock_info(symbol)
                passes, reason = self.passes_quality_filters(stock_info)
                
                if passes:
                    approved.append(symbol)
                    print(f"   ✅ {symbol}: {stock_info.get('short_name', '')}")
                else:
                    rejected[symbol] = reason
                    print(f"   ❌ {symbol}: {reason}")
            
            # Pausa entre lotes para evitar rate limiting
            if i + batch_size < len(symbols):
                time.sleep(2)
        
        # Estadísticas
        print(f"\n{'='*50}")
        print(f"📊 RESUMEN DE FILTRADO:")
        print(f"   ✅ Aprobados: {len(approved)}/{len(symbols)} ({len(approved)/len(symbols)*100:.1f}%)")
        print(f"   ❌ Rechazados: {len(rejected)}/{len(symbols)}")
        
        # Top razones de rechazo
        if rejected:
            reasons_count = {}
            for reason in rejected.values():
                key = reason.split(':')[0] if ':' in reason else reason
                reasons_count[key] = reasons_count.get(key, 0) + 1
            
            print(f"\n   📉 Principales razones de rechazo:")
            for reason, count in sorted(reasons_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      • {reason}: {count}")
        
        print(f"{'='*50}\n")
        
        return approved
