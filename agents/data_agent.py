import yfinance as yf
import pandas as pd
import numpy as np
import time

class DataAgent:
    def __init__(self, symbols, config):
        self.symbols = symbols
        self.config = config
        self.lookback_days = config.get("lookback_days", 90)
        self.batch_size = 50
        self.sleep_sec = 2

    def compute_rsi(self, series, period=14):
        """Calcula el RSI (Relative Strength Index)."""
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def compute_macd(self, series, fast=12, slow=26, signal=9):
        """Calcula el MACD (Moving Average Convergence Divergence)."""
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def compute_stochastic(self, df, k_period=14, d_period=3, smooth=3):
        """Calcula el Stochastic Oscillator."""
        low_min = df["Low"].rolling(k_period).min()
        high_max = df["High"].rolling(k_period).max()
        k = 100 * (df["Close"] - low_min) / (high_max - low_min)
        k_smooth = k.rolling(smooth).mean()
        d = k_smooth.rolling(d_period).mean()
        return k_smooth, d

    def compute_atr(self, df, period=14):
        """Calcula el Average True Range."""
        high_low = df["High"] - df["Low"]
        high_close = abs(df["High"] - df["Close"].shift())
        low_close = abs(df["Low"] - df["Close"].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.rolling(period).mean()

    def compute_adx(self, df, period=14):
        """Calcula el Average Directional Index."""
        plus_dm = df["High"].diff()
        minus_dm = -df["Low"].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = self.compute_atr(df, 1)
        plus_di = 100 * (plus_dm.rolling(period).mean() / tr.rolling(period).mean())
        minus_di = 100 * (minus_dm.rolling(period).mean() / tr.rolling(period).mean())
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        return adx

    def compute_keltner_channels(self, df, period=20, multiplier=2):
        """Calcula los Keltner Channels."""
        ema = df["Close"].ewm(span=period, adjust=False).mean()
        atr = self.compute_atr(df, period)
        upper = ema + (multiplier * atr)
        lower = ema - (multiplier * atr)
        return upper, ema, lower

    def compute_supertrend(self, df, period=7, multiplier=3):
        """Calcula el SuperTrend."""
        atr = self.compute_atr(df, period)
        hl_avg = (df["High"] + df["Low"]) / 2
        
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=float)
        
        for i in range(period, len(df)):
            if df["Close"].iloc[i] > upper_band.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif df["Close"].iloc[i] < lower_band.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]
        
        return supertrend, direction

    def compute_vwap(self, df):
        """Calcula el VWAP (Volume Weighted Average Price)."""
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        return (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()

    def compute_trend(self, df, window=20):
        """Determina la tendencia del activo."""
        if len(df) < window:
            return "lateral"
        
        recent_prices = df["Close"].tail(window)
        slope = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / window
        
        if slope > 0.5:
            return "alcista"
        elif slope < -0.5:
            return "bajista"
        else:
            return "lateral"

    def batch_download(self):
        """Descarga datos en lotes y calcula TODOS los indicadores."""
        results = []
        indicators_config = self.config.get("indicators", {})
        
        print(f"📥 Descargando {len(self.symbols)} símbolos...")

        for i in range(0, len(self.symbols), self.batch_size):
            batch = self.symbols[i:i+self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(self.symbols) + self.batch_size - 1) // self.batch_size
            print(f"📦 Lote {batch_num}/{total_batches}...")

            try:
                df_all = yf.download(
                    batch,
                    period=f"{self.lookback_days}d",
                    interval="1d",
                    progress=False,
                    group_by="ticker",
                    auto_adjust=True
                )

                for s in batch:
                    try:
                        if len(batch) == 1:
                            df = df_all.copy()
                        else:
                            df = df_all[s].copy()

                        if df.empty or len(df) < 60:
                            continue

                        # EMAs
                        df["EMA_short"] = df["Close"].ewm(span=indicators_config.get("ema_short", 5), adjust=False).mean()
                        df["EMA_long"] = df["Close"].ewm(span=indicators_config.get("ema_long", 20), adjust=False).mean()
                        df["EMA_trend"] = df["Close"].ewm(span=indicators_config.get("ema_trend", 50), adjust=False).mean()
                        
                        # RSI
                        df["RSI"] = self.compute_rsi(df["Close"], indicators_config.get("rsi_period", 9))
                        
                        # Stochastic
                        stoch_params = indicators_config.get("stochastic", [9, 3, 3])
                        df["Stoch_K"], df["Stoch_D"] = self.compute_stochastic(df, *stoch_params)
                        
                        # MACD
                        macd_params = [
                            indicators_config.get("macd_fast", 5),
                            indicators_config.get("macd_slow", 13),
                            indicators_config.get("macd_signal", 5)
                        ]
                        df["MACD"], df["MACD_Signal"], df["MACD_Histogram"] = self.compute_macd(df["Close"], *macd_params)
                        
                        # ATR
                        df["ATR"] = self.compute_atr(df, indicators_config.get("atr_period", 7))
                        
                        # ADX
                        df["ADX"] = self.compute_adx(df, indicators_config.get("adx_period", 14))
                        
                        # Keltner Channels
                        kelt_period = indicators_config.get("keltner_period", 10)
                        kelt_mult = indicators_config.get("keltner_multiplier", 2.0)
                        df["Keltner_Upper"], df["Keltner_Mid"], df["Keltner_Lower"] = self.compute_keltner_channels(df, kelt_period, kelt_mult)
                        
                        # SuperTrend
                        st_period = indicators_config.get("supertrend_period", 7)
                        st_mult = indicators_config.get("supertrend_multiplier", 1.5)
                        df["SuperTrend"], df["ST_Direction"] = self.compute_supertrend(df, st_period, st_mult)
                        
                        # VWAP (últimos 20 días para que sea relevante)
                        df["VWAP"] = self.compute_vwap(df.tail(20))
                        
                        # Volumen
                        df["Volume_MA"] = df["Volume"].rolling(20).mean()
                        df["Volume_Ratio"] = df["Volume"] / df["Volume_MA"]
                        
                        # Momentum y volatilidad
                        df["Momentum"] = df["Close"].pct_change(5)
                        df["Volatility"] = df["Close"].pct_change().rolling(10).std()
                        
                        # Soporte/Resistencia
                        df["Support"] = df["Low"].rolling(20).min()
                        df["Resistance"] = df["High"].rolling(20).max()

                        # Obtener último valor
                        latest = df.iloc[-1]
                        close = float(latest["Close"])
                        
                        # ATR en porcentaje del precio
                        atr_pct = (float(latest["ATR"]) / close) * 100

                        results.append({
                            "symbol": s,
                            "close": round(close, 2),
                            "ema_short": round(float(latest["EMA_short"]), 2),
                            "ema_long": round(float(latest["EMA_long"]), 2),
                            "ema_trend": round(float(latest["EMA_trend"]), 2),
                            "rsi": round(float(latest["RSI"]), 2),
                            "stoch_k": round(float(latest["Stoch_K"]), 2),
                            "stoch_d": round(float(latest["Stoch_D"]), 2),
                            "macd": round(float(latest["MACD"]), 4),
                            "macd_signal": round(float(latest["MACD_Signal"]), 4),
                            "macd_histogram": round(float(latest["MACD_Histogram"]), 4),
                            "atr": round(float(latest["ATR"]), 2),
                            "atr_pct": round(atr_pct, 2),
                            "adx": round(float(latest["ADX"]), 2),
                            "keltner_upper": round(float(latest["Keltner_Upper"]), 2),
                            "keltner_mid": round(float(latest["Keltner_Mid"]), 2),
                            "keltner_lower": round(float(latest["Keltner_Lower"]), 2),
                            "supertrend": round(float(latest["SuperTrend"]), 2),
                            "st_direction": int(latest["ST_Direction"]),
                            "vwap": round(float(latest["VWAP"]), 2),
                            "momentum": round(float(latest["Momentum"]), 4),
                            "volatility": round(float(latest["Volatility"]), 4),
                            "volume_ratio": round(float(latest["Volume_Ratio"]), 2),
                            "support": round(float(latest["Support"]), 2),
                            "resistance": round(float(latest["Resistance"]), 2),
                            "trend": self.compute_trend(df)
                        })

                    except Exception as e:
                        print(f"⚠️ Error procesando {s}: {e}")
                        continue

            except Exception as e:
                print(f"⚠️ Error en lote: {e}")

            if i + self.batch_size < len(self.symbols):
                time.sleep(self.sleep_sec)

        print(f"✅ Descarga completa: {len(results)} activos procesados.")
        return results
