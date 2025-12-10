import pandas as pd

class SelectorAgent:
    def __init__(self, config):
        self.config = config

    def select_top(self, results):
        """
        Selecciona solo las mejores oportunidades.
        Para capital limitado (€2k-5k): Máxima selectividad.
        """
        if not results:
            return []

        # Normalizar estructura
        items = []
        if isinstance(results, dict):
            items = [{"symbol": sym, **metrics} for sym, metrics in results.items() if isinstance(metrics, dict)]
        elif isinstance(results, list):
            for el in results:
                if isinstance(el, tuple) and len(el) == 2:
                    symbol, metrics = el
                    if isinstance(metrics, dict):
                        metrics["symbol"] = symbol
                        items.append(metrics)
                elif isinstance(el, dict):
                    items.append(el)
        else:
            return []

        if not items:
            return []

        df = pd.DataFrame(items)

        # Filtros de calidad ESTRICTOS
        df = df.dropna(subset=["score", "rsi", "rr_ratio_2"])
        
        # Solo score >= 8.0 (ya viene filtrado del Analysis Agent, pero por si acaso)
        df = df[df["score"] >= 8.0]
        
        # Ratio R/R mínimo de 5:1 para target 2
        min_rr = self.config.get("targets", {}).get("min_risk_reward_ratio", 5.0)
        df = df[df["rr_ratio_2"] >= min_rr]
        
        # Eliminar valores con volatilidad extrema (ATR > 2%)
        df = df[df["atr_pct"] <= 2.0]
        
        # Ordenar por score (ya viene ordenado, pero reforzamos)
        df = df.sort_values(by="score", ascending=False)

        # Seleccionar top N
        top_n = self.config.get("top_n", 3)
        top_assets = df.head(top_n).to_dict(orient="records")

        # Estadísticas
        if top_assets:
            avg_score = sum(a["score"] for a in top_assets) / len(top_assets)
            strong_signals = sum(1 for a in top_assets if a["score"] >= 8.5)
            avg_rr = sum(a["rr_ratio_2"] for a in top_assets) / len(top_assets)
            
            print(f"✅ Selección final: {len(top_assets)} oportunidades de {len(items)} candidatos")
            print(f"   📊 Score promedio: {avg_score:.2f}/10")
            print(f"   🟢 Señales MUY FUERTES (8.5+): {strong_signals}/{len(top_assets)}")
            print(f"   💎 R/R promedio: {avg_rr:.1f}:1")
        else:
            print("⚠️ No hay activos que cumplan todos los criterios esta semana.")
        
        return top_assets
