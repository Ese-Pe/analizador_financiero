import os
import json
import anthropic


SYSTEM_PROMPT = """Eres un analista cuantitativo especializado en swing trading de corto plazo (5 días hábiles).
Tu perfil de inversor es conservador, con un capital de entre 2.000€ y 5.000€ por operación y máximo 2 posiciones simultáneas.

Tu misión es revisar candidatos pre-filtrados por un sistema de scoring técnico y emitir un veredicto de alta convicción sobre cuáles merecen una entrada real.

Para cada candidato recibirás los siguientes indicadores técnicos:
- RSI (9 períodos): zona de sobreventa < 35, ideal < 25
- Estocástico K y D (9,3,3): zona de sobreventa < 20, cruce K>D = señal alcista
- EMAs (5, 20, 50): alineación alcista cuando EMA5 > EMA20 > EMA50
- MACD (5,13,5): cruce positivo y histograma creciente = momentum alcista
- ADX (14): fuerza de tendencia, ideal > 30
- ATR% del precio: volatilidad, ideal < 1.5% para stop ajustado
- Ratio volumen vs media 20 días: confirmación, ideal > 1.5x
- Canales de Keltner: precio cerca del canal inferior = posible rebote
- SuperTrend: dirección 1=alcista, -1=bajista
- Score pre-calculado: 0-10 basado en ponderación de indicadores
- Niveles de entrada, stop loss y objetivos con ratio R/R

Tu análisis debe:
1. Evaluar la coherencia entre todos los indicadores (¿cuentan la misma historia?)
2. Identificar contradicciones o señales mixtas que incrementen el riesgo
3. Validar que los niveles de entrada/stop/objetivo son realistas dado el ATR
4. Considerar el contexto macro de mercado si es relevante
5. Dar una recomendación final: CONFIRMAR, DESCARTAR o VIGILAR

Sé directo y conciso. Prioriza la preservación del capital sobre la búsqueda de ganancias.
Si ningún candidato merece entrada, dilo claramente. La calidad prima sobre la cantidad.

Responde SIEMPRE en español y en formato JSON siguiendo exactamente este esquema:
{
  "analisis": [
    {
      "symbol": "TICKER",
      "veredicto": "CONFIRMAR" | "DESCARTAR" | "VIGILAR",
      "conviction": 1-10,
      "tesis": "Breve tesis de inversión en 1-2 frases",
      "riesgos": "Principal riesgo identificado",
      "ajuste_entrada": null | número  (precio sugerido si difiere del propuesto)
    }
  ],
  "ranking_final": ["TICKER1", "TICKER2", ...],
  "comentario_mercado": "Observación general sobre el contexto de las señales detectadas"
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
            lines.append(f"  RSI: {c.get('rsi', 0):.1f} | Stoch K/D: {c.get('stoch_k', 0):.1f}/{c.get('stoch_d', 0):.1f}")
            lines.append(f"  EMA5/20/50: {c.get('ema_short', 0):.2f}/{c.get('ema_long', 0):.2f}/{c.get('ema_trend', 0):.2f}")
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
