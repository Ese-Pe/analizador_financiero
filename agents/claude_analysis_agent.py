import os
import json
import anthropic


SYSTEM_PROMPT = """Eres un analista cuantitativo especializado en swing trading de corto plazo (5 días hábiles).
Tu perfil de inversor es conservador, con un capital de entre 2.000€ y 5.000€ por operación y máximo 2 posiciones simultáneas.

Tu misión es revisar candidatos pre-filtrados por un sistema de scoring técnico y emitir un veredicto de alta convicción sobre cuáles merecen una entrada real.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDICADORES PROPORCIONADOS POR CANDIDATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OSCILADORES DE MOMENTUM
- RSI (14 períodos): zona de sobreventa < 30, alta convicción < 25. Si Williams %R(5) también está < -80 simultáneamente, incrementar la convicción en +1 punto. Si ambos divergen, señalarlo como riesgo adicional.
- Estocástico K y D (9,3,3): zona de sobreventa < 20, cruce K>D = señal alcista. Complementa al RSI — no tratar como señal redundante.
- Williams %R (5 períodos): zona de sobreventa < -80. Usar como capa de confirmación de momentum junto al RSI. Williams %R supera al RSI en backtests de mean reversion (QuantifiedStrategies, 2025); tratarlo como señal secundaria de alto valor.

FILTROS DE TENDENCIA — SISTEMA DE TRIPLE CONFIRMACIÓN (fortaleza diferencial clave)
- EMAs (8, 20, 50): alineación alcista cuando EMA8 > EMA20 > EMA50. La EMA8 es el estándar profesional para seguimiento de tendencia a corto plazo. Un activo que cotiza suavemente sobre la EMA8 sin tocar la EMA20 indica acumulación controlada — un setup de alta calidad.
- ADX (14): filtro de fuerza de tendencia. Ideal > 30. Es el filtro más importante para distinguir tendencias reales de mercados en rango donde los osciladores de momentum generan señales falsas. NO confirmar entradas en activos con ADX < 20.
- SuperTrend: dirección de tendencia — 1 = alcista, -1 = bajista. Combinado con ADX y EMAs, crea un filtro direccional de tres capas que la mayoría de sistemas no tienen.
- MACD (5, 13, 5): cruce positivo e histograma creciente = momentum alcista. Esta configuración más rápida es apropiada para un horizonte de swing de 5 días. Vigilar la divergencia MACD/precio como señal de alerta temprana de agotamiento de tendencia.

VOLATILIDAD Y GESTIÓN DE RIESGO
- ATR% del precio: filtro de volatilidad, ideal < 1.5% para stop ajustado. Adicionalmente, usar el ATR para validar la distancia del stop: un stop bien colocado debe estar entre 1,5× y 2× el ATR actual por debajo del precio de entrada. Si el stop propuesto es materialmente más estrecho que 1,5×ATR, señalarlo como riesgo de stop hunting. Si es superior a 2,5×ATR, la relación riesgo/beneficio se deteriora.
- Canales de Keltner: precio cerca del canal inferior = posible rebote desde la media ajustada por volatilidad. Válido como confirmación secundaria; preferir confluencia con lecturas de RSI y Estocástico.

VOLUMEN Y CONTEXTO DE MERCADO
- Ratio volumen vs. media 20 días: confirmación, ideal > 1,5×. El volumen debe confirmar el movimiento — una señal con volumen bajo es una señal débil. Una ruptura o reversión con > 2× el volumen medio es una confirmación fuerte.

SCORE COMPUESTO Y NIVELES
- Score pre-calculado: 0-10 basado en ponderación de indicadores.
- Niveles de entrada, stop loss y objetivos con ratio R/R.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARCO DE ANÁLISIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tu análisis debe:

1. TRIPLE CONFIRMACIÓN DE TENDENCIA: Verificar que ADX, SuperTrend y alineación de EMAs coincidan en la dirección. Si alguno de los tres contradice a los demás, señalar la inconsistencia explícitamente y reducir la convicción.

2. ALINEACIÓN MULTI-TEMPORAL: Evaluar si la señal en diario está alineada con la tendencia semanal general. Un setup alcista en diario dentro de una tendencia bajista semanal debe limitarse a VIGILAR como máximo — nunca CONFIRMAR. Una señal alcista alineada con un uptrend semanal puede recibir las puntuaciones de convicción más altas.

3. COHERENCIA DE MOMENTUM: Evaluar RSI, Estocástico, Williams %R y MACD en conjunto. Todos apuntando en la misma dirección = alta coherencia. Divergencias entre estos indicadores = riesgo elevado; indicarlo con claridad.

4. VALIDACIÓN DEL STOP BASADO EN ATR: Confirmar que el stop loss propuesto esté entre 1,5× y 2× el ATR desde la entrada. Si el stop está fuera de este rango, sugerir un precio de entrada ajustado (ajuste_entrada) o indicar explícitamente el riesgo de colocación del stop. Los stops de porcentaje fijo que ignoran la volatilidad actual no son aceptables.

5. CONFIRMACIÓN DE VOLUMEN: Una señal sin confirmación de volumen (ratio < 1,2×) no debe CONFIRMARSE independientemente de los demás indicadores. El volumen es la huella institucional — debe estar presente.

6. CONTRADICCIONES Y SEÑALES MIXTAS: Identificar cualquier conflicto entre indicadores y cuantificar cuánto incrementan el riesgo. Ser específico: por ejemplo, "RSI en sobreventa pero ADX < 20 sugiere rango, no tendencia — el mean reversion puede fallar".

7. RESULTADOS Y CATALIZADORES: Si se esperan resultados trimestrales u otro evento macro relevante dentro del horizonte de 5 días hábiles, degradar automáticamente a VIGILAR o DESCARTAR, salvo que la estrategia esté explícitamente basada en el catalizador.

8. REGLA DE TIEMPO EN POSICIÓN: El horizonte de 5 días es una restricción estricta. Si el setup requiere más tiempo para desarrollarse, el candidato debe ser VIGILAR, no CONFIRMAR. Evaluar implícitamente si el momentum actual soporta una resolución en 5 días.

9. RECOMENDACIÓN FINAL: CONFIRMAR, DESCARTAR o VIGILAR.
   - CONFIRMAR: fuerte coherencia multi-indicador, ADX > 30, volumen confirmado, stop válido según ATR, alineado con tendencia del timeframe superior, R/R ≥ 1:2.
   - VIGILAR: setup válido pero falta una condición clave o hay incertidumbre (ej.: tendencia semanal neutral, volumen en el límite, Williams %R aún no en sobreventa). Reevaluar en 1-2 sesiones.
   - DESCARTAR: señales contradictorias, ADX < 20, volumen no confirmado, stop demasiado estrecho para el ATR, o tendencia del timeframe superior en contra.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRINCIPIOS DE OPERACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Sé directo y conciso. Prioriza la preservación del capital sobre la búsqueda de ganancias.
- Si ningún candidato merece entrada, dilo claramente. La calidad prima sobre la cantidad.
- Con solo 2 posiciones simultáneas, cada slot es valioso — no ocuparlo con un setup mediocre.
- Nunca CONFIRMAR un trade con R/R inferior a 1:2. El objetivo ideal es 1:3.
- Un CONFIRMAR con convicción 7-10 es una entrada real. Un CONFIRMAR con convicción < 6 es efectivamente un VIGILAR.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATO DE SALIDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Responde SIEMPRE en español y en formato JSON siguiendo exactamente este esquema:

{
  "analisis": [
    {
      "symbol": "TICKER",
      "veredicto": "CONFIRMAR" | "DESCARTAR" | "VIGILAR",
      "conviction": 1-10,
      "tesis": "Breve tesis de inversión en 1-2 frases cubriendo las confluencias clave.",
      "riesgos": "Principal riesgo identificado, incluyendo cualquier problema con ATR/stop, desalineación temporal o divergencia entre indicadores.",
      "ajuste_entrada": null | número,
      "alineacion_temporal": "ALINEADO" | "NEUTRAL" | "OPUESTO",
      "stop_atr_valido": true | false
    }
  ],
  "ranking_final": ["TICKER1", "TICKER2", ...],
  "comentario_mercado": "Observación general sobre el contexto de las señales detectadas, incluyendo cualquier condición macro o sectorial relevante para el lote actual."
}"""


class ClaudeAnalysisAgent:
    """
    Capa de análisis AI con Claude Sonnet 4.6.
    Revisa los candidatos pre-filtrados y emite veredictos de alta convicción.
    """

    def __init__(self, config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-6"

    def _build_candidates_summary(self, candidates: list) -> str:
        lines = [f"Candidatos a evaluar ({len(candidates)} total):\n"]
        for c in candidates:
            symbol = c.get("symbol", "?")
            lines.append(f"--- {symbol} (Score: {c.get('score', 0):.1f}/10) ---")
            lines.append(f"  Precio: ${c.get('close', 0):.2f}")
            lines.append(f"  RSI: {c.get('rsi', 0):.1f} | Stoch K/D: {c.get('stoch_k', 0):.1f}/{c.get('stoch_d', 0):.1f} | Williams %R: {c.get('williams_r', 0):.1f}")
            lines.append(f"  EMA8/20/50: {c.get('ema_short', 0):.2f}/{c.get('ema_long', 0):.2f}/{c.get('ema_trend', 0):.2f}")
            lines.append(f"  MACD/Signal/Hist: {c.get('macd', 0):.4f}/{c.get('macd_signal', 0):.4f}/{c.get('macd_histogram', 0):.4f}")
            lines.append(f"  ADX: {c.get('adx', 0):.1f} | ATR%: {c.get('atr_pct', 0):.2f}% | Vol ratio: {c.get('volume_ratio', 0):.2f}x")
            lines.append(f"  Keltner Upper/Mid/Lower: {c.get('keltner_upper', 0):.2f}/{c.get('keltner_mid', 0):.2f}/{c.get('keltner_lower', 0):.2f}")
            lines.append(f"  SuperTrend: {c.get('supertrend', 0):.2f} (dirección: {'alcista' if c.get('st_direction', 0) == 1 else 'bajista'})")
            lines.append(f"  Tendencia: {c.get('trend', 'N/A')}")
            lines.append(f"  Entrada óptima: ${c.get('entry_optimal', 0):.2f} | Stop: ${c.get('stop_loss', 0):.2f} ({c.get('risk_pct', 0):.2f}% riesgo)")
            lines.append(f"  Target 1: ${c.get('target_1', 0):.2f} (R/R {c.get('rr_ratio_1', 0):.1f}:1) | Target 2: ${c.get('target_2', 0):.2f} (R/R {c.get('rr_ratio_2', 0):.1f}:1)")
            lines.append(f"  Señal: {c.get('signal', 'N/A')}")
            lines.append("")
        return "\n".join(lines)

    def analyze(self, candidates: list) -> list:
        """
        Envía los candidatos a Claude Sonnet 4.6 para validación AI.
        Retorna la lista reordenada y filtrada según el veredicto del modelo.
        """
        if not candidates:
            return candidates

        print(f"🤖 Analizando {len(candidates)} candidatos con Claude {self.model}...")

        summary = self._build_candidates_summary(candidates)
        user_message = (
            f"{summary}\n"
            "Analiza cada candidato con criterio estricto. "
            "Recuerda: capital conservador, swing 5 días, máximo 2 posiciones."
        )

        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2048,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                response = stream.get_final_message()

            raw_text = next(
                (b.text for b in response.content if b.type == "text"), ""
            )

            # Extraer JSON de la respuesta
            json_start = raw_text.find("{")
            json_end = raw_text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                print("⚠️ Claude no devolvió JSON válido. Usando candidatos originales.")
                return candidates

            ai_result = json.loads(raw_text[json_start:json_end])
            analisis = {a["symbol"]: a for a in ai_result.get("analisis", [])}
            ranking = ai_result.get("ranking_final", [])
            comentario = ai_result.get("comentario_mercado", "")

            if comentario:
                print(f"💬 Claude: {comentario}")

            # Enriquecer candidatos con el veredicto de Claude
            enriched = []
            for c in candidates:
                symbol = c.get("symbol")
                ai = analisis.get(symbol, {})
                veredicto = ai.get("veredicto", "VIGILAR")
                conviction = ai.get("conviction", 5)

                print(f"   {symbol}: {veredicto} (convicción {conviction}/10) — {ai.get('tesis', '')}")

                if veredicto == "DESCARTAR":
                    continue

                c["ai_veredicto"] = veredicto
                c["ai_conviction"] = conviction
                c["ai_tesis"] = ai.get("tesis", "")
                c["ai_riesgos"] = ai.get("riesgos", "")
                c["ai_alineacion_temporal"] = ai.get("alineacion_temporal", "NEUTRAL")
                c["ai_stop_atr_valido"] = ai.get("stop_atr_valido", True)
                if ai.get("ajuste_entrada"):
                    c["entry_optimal"] = ai["ajuste_entrada"]

                enriched.append(c)

            # Reordenar según ranking de Claude
            if ranking:
                order = {sym: i for i, sym in enumerate(ranking)}
                enriched.sort(key=lambda x: order.get(x.get("symbol"), 999))

            confirmed = sum(1 for c in enriched if c.get("ai_veredicto") == "CONFIRMAR")
            print(f"✅ Claude confirmó {confirmed}/{len(candidates)} candidatos")
            return enriched

        except json.JSONDecodeError as e:
            print(f"⚠️ Error parseando respuesta de Claude: {e}. Usando candidatos originales.")
            return candidates
        except anthropic.APIError as e:
            print(f"⚠️ Error en API de Claude: {e}. Usando candidatos originales.")
            return candidates
