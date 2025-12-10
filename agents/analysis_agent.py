import pandas as pd

class AnalysisAgent:
    def __init__(self, config):
        self.config = config
        self.thresholds = config.get("signal_thresholds", {})
        self.weights = config.get("scoring", {})

    def calculate_score(self, asset):
        """
        Sistema de scoring ultra-preciso para capital limitado.
        Cada punto cuenta. Score 8.5+ = señal de alta probabilidad.
        """
        score = 0.0
        
        # 1. RSI Score (20% del total) - Prioridad en sobreventa
        rsi = asset.get("rsi", 50)
        if rsi < 20:
            rsi_score = 10  # Sobreventa extrema
        elif rsi < 25:
            rsi_score = 9
        elif rsi < 30:
            rsi_score = 8
        elif rsi < 35:
            rsi_score = 6
        elif rsi < 45:
            rsi_score = 4
        else:
            rsi_score = 2
        score += rsi_score * self.weights.get("rsi_weight", 0.20)
        
        # 2. Stochastic Score (15% del total) - Confirma sobreventa
        stoch_k = asset.get("stoch_k", 50)
        stoch_d = asset.get("stoch_d", 50)
        stoch_cross = stoch_k > stoch_d  # Cruce alcista
        
        if stoch_k < 15 and stoch_cross:
            stoch_score = 10  # Sobreventa + cruce alcista
        elif stoch_k < 20 and stoch_cross:
            stoch_score = 9
        elif stoch_k < 20:
            stoch_score = 7
        elif stoch_k < 30:
            stoch_score = 5
        else:
            stoch_score = 3
        score += stoch_score * self.weights.get("stochastic_weight", 0.15)
        
        # 3. EMAs Score (15% del total) - Tendencia
        ema_short = asset.get("ema_short", 0)
        ema_long = asset.get("ema_long", 0)
        ema_trend = asset.get("ema_trend", 0)
        close = asset.get("close", 0)
        
        if ema_short > ema_long > ema_trend:
            ema_score = 10  # Tendencia alcista clara
        elif ema_short > ema_long:
            ema_score = 8  # Cruce alcista reciente
        elif ema_short > ema_trend:
            ema_score = 6
        else:
            ema_score = 3
        score += ema_score * self.weights.get("ema_weight", 0.15)
        
        # 4. MACD Score (15% del total) - Momentum
        macd = asset.get("macd", 0)
        macd_signal = asset.get("macd_signal", 0)
        macd_hist = asset.get("macd_histogram", 0)
        
        if macd > macd_signal and macd_hist > 0 and macd_hist > asset.get("prev_macd_hist", 0):
            macd_score = 10  # Cruce alcista con momentum creciente
        elif macd > macd_signal and macd_hist > 0:
            macd_score = 8
        elif macd > macd_signal:
            macd_score = 6
        elif macd_hist > 0:
            macd_score = 4
        else:
            macd_score = 2
        score += macd_score * self.weights.get("macd_weight", 0.15)
        
        # 5. Volumen Score (15% del total) - Confirmación
        volume_ratio = asset.get("volume_ratio", 1.0)
        if volume_ratio > 2.5:
            volume_score = 10  # Volumen explosivo
        elif volume_ratio > 2.0:
            volume_score = 9
        elif volume_ratio > 1.8:
            volume_score = 8
        elif volume_ratio > 1.5:
            volume_score = 6
        elif volume_ratio > 1.2:
            volume_score = 4
        else:
            volume_score = 2
        score += volume_score * self.weights.get("volume_weight", 0.15)
        
        # 6. Volatilidad/ATR Score (10% del total) - Para stop loss ajustado
        atr_pct = asset.get("atr_pct", 2.0)
        if atr_pct < 0.8:
            volatility_score = 10  # Muy estable
        elif atr_pct < 1.2:
            volatility_score = 9  # Ideal para stop 1%
        elif atr_pct < 1.5:
            volatility_score = 7  # Aceptable
        elif atr_pct < 2.0:
            volatility_score = 5
        else:
            volatility_score = 2  # Demasiado volátil
        score += volatility_score * self.weights.get("volatility_weight", 0.10)
        
        # 7. ADX Score (10% del total) - Fuerza de tendencia
        adx = asset.get("adx", 0)
        if adx > 40:
            adx_score = 10  # Tendencia muy fuerte
        elif adx > 30:
            adx_score = 9
        elif adx > 25:
            adx_score = 7
        elif adx > 20:
            adx_score = 5
        else:
            adx_score = 2  # Sin tendencia clara
        score += adx_score * self.weights.get("adx_weight", 0.10)
        
        return round(score, 2)

    def get_signal_strength(self, score):
        """Clasifica la señal según score."""
        green_threshold = self.weights.get("green_threshold", 8.5)
        yellow_threshold = self.weights.get("yellow_threshold", 8.0)
        
        if score >= green_threshold:
            return "🟢", "MUY FUERTE"
        elif score >= yellow_threshold:
            return "🟡", "FUERTE"
        else:
            return "🔴", "DÉBIL"

    def calculate_entry_exit_levels(self, asset):
        """Calcula niveles exactos de entrada, objetivo y stop loss."""
        close = asset.get("close", 0)
        atr = asset.get("atr", 0)
        keltner_lower = asset.get("keltner_lower", close)
        keltner_mid = asset.get("keltner_mid", close)
        keltner_upper = asset.get("keltner_upper", close)
        supertrend = asset.get("supertrend", close)
        vwap = asset.get("vwap", close)
        
        targets_config = self.config.get("targets", {})
        
        # Precio de entrada óptimo (entre precio actual y Keltner inferior)
        entry_optimal = min(close, keltner_lower * 1.002)  # 0.2% por encima de Keltner
        
        # Stop loss: 1% o SuperTrend, lo que sea más cercano
        stop_loss_pct = targets_config.get("stop_loss_pct", 1.0) / 100
        stop_loss_price = close * (1 - stop_loss_pct)
        stop_loss_supertrend = supertrend if supertrend < close else stop_loss_price
        stop_loss = max(stop_loss_price, stop_loss_supertrend)  # El más conservador
        
        # Objetivos de beneficio
        target_conservative = close * (1 + targets_config.get("profit_target_conservative", 5.0) / 100)
        target_normal = close * (1 + targets_config.get("profit_target_pct", 7.0) / 100)
        target_aggressive = close * (1 + targets_config.get("profit_target_aggressive", 10.0) / 100)
        
        # Ajustar objetivos según Keltner
        target_1 = min(target_conservative, keltner_mid)
        target_2 = min(target_normal, keltner_upper * 0.98)
        target_3 = target_aggressive
        
        # Calcular ratios riesgo/beneficio
        risk = close - stop_loss
        reward_1 = target_1 - close
        reward_2 = target_2 - close
        reward_3 = target_3 - close
        
        rr_ratio_1 = reward_1 / risk if risk > 0 else 0
        rr_ratio_2 = reward_2 / risk if risk > 0 else 0
        rr_ratio_3 = reward_3 / risk if risk > 0 else 0
        
        return {
            "entry_optimal": round(entry_optimal, 2),
            "entry_max": round(close, 2),
            "stop_loss": round(stop_loss, 2),
            "target_1": round(target_1, 2),
            "target_2": round(target_2, 2),
            "target_3": round(target_3, 2),
            "rr_ratio_1": round(rr_ratio_1, 2),
            "rr_ratio_2": round(rr_ratio_2, 2),
            "rr_ratio_3": round(rr_ratio_3, 2),
            "risk_pct": round((risk / close) * 100, 2),
            "reward_1_pct": round((reward_1 / close) * 100, 2),
            "reward_2_pct": round((reward_2 / close) * 100, 2),
            "reward_3_pct": round((reward_3 / close) * 100, 2)
        }

    def analyze(self, data_list):
        """Analiza y filtra solo las mejores oportunidades."""
        results = []
        print("🔬 Analizando con criterios ultra-estrictos...")

        for asset in data_list:
            try:
                # Validaciones básicas
                required_fields = ["rsi", "ema_short", "ema_long", "macd", "macd_signal", "adx", "atr_pct"]
                if any(asset.get(f) is None or pd.isna(asset.get(f)) for f in required_fields):
                    continue

                # FILTRO PRE-SCORE: Eliminar valores que no cumplen mínimos
                rsi = asset.get("rsi", 50)
                adx = asset.get("adx", 0)
                atr_pct = asset.get("atr_pct", 5.0)
                volume_ratio = asset.get("volume_ratio", 0)
                
                # Criterios eliminatorios
                if rsi > 40:  # Debe estar en zona de sobreventa
                    continue
                if adx < self.thresholds.get("adx_min", 25):  # Tendencia debe ser fuerte
                    continue
                if atr_pct > self.thresholds.get("max_volatility_atr_pct", 1.5):  # Volatilidad controlada
                    continue
                if volume_ratio < 1.3:  # Debe haber interés
                    continue
                
                # Calcular score
                score = self.calculate_score(asset)
                
                # Solo procesar si score >= 8.0
                if score < 8.0:
                    continue
                
                indicator, strength = self.get_signal_strength(score)
                levels = self.calculate_entry_exit_levels(asset)
                
                # Validar ratio R/R mínimo
                min_rr = self.config.get("targets", {}).get("min_risk_reward_ratio", 5.0)
                if levels["rr_ratio_2"] < min_rr:
                    continue  # No cumple R/R mínimo
                
                # Determinar tipo de señal
                ema_short = asset.get("ema_short", 0)
                ema_long = asset.get("ema_long", 0)
                close = asset.get("close", 0)
                keltner_lower = asset.get("keltner_lower", 0)
                
                if rsi < 25 and close <= keltner_lower * 1.01:
                    signal = "🎯 Rebote alcista PREMIUM"
                elif rsi < 30 and ema_short > ema_long:
                    signal = "📈 Rebote alcista confirmado"
                elif 30 <= rsi <= 35:
                    signal = "⚡ Corrección controlada"
                else:
                    signal = "✅ Oportunidad de entrada"
                
                results.append({
                    **asset,
                    "score": score,
                    "indicator": indicator,
                    "strength": strength,
                    "signal": signal,
                    **levels
                })

            except Exception as e:
                print(f"⚠️ Error analizando {asset.get('symbol', '?')}: {e}")

        # Ordenar por score descendente
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        
        print(f"✅ Análisis completado: {len(results)} señales de calidad 8+/10 detectadas.")
        return results
