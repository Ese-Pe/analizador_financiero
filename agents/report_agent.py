import os
import requests
import datetime

class ReportAgent:
    def __init__(self, token=None, chat_id=None, report_type="detailed"):
        self.token = token or os.getenv("TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.report_type = report_type  # "detailed" o "update"

        if not self.token:
            print("⚠️ TELEGRAM_TOKEN no está configurado.")
        if not self.chat_id:
            print("⚠️ TELEGRAM_CHAT_ID no está configurado.")

    def format_detailed_report(self, top_assets):
        """Informe VIERNES: Análisis profundo para planificar la semana."""
        now = datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')
        day_name = datetime.datetime.utcnow().strftime('%A').upper()
        
        # Header
        header = (
            f"{'═' * 40}\n"
            f"📊 *INFORME SEMANAL - {day_name}*\n"
            f"🕐 {now}\n"
            f"{'═' * 40}\n\n"
        )
        
        if not top_assets:
            return header + "⚠️ No hay oportunidades que cumplan los criterios esta semana.\n"
        
        # Resumen ejecutivo
        avg_score = sum(a.get("score", 0) for a in top_assets) / len(top_assets)
        strong_signals = sum(1 for a in top_assets if a.get("score", 0) >= 8.5)
        avg_rr = sum(a.get("rr_ratio_2", 0) for a in top_assets) / len(top_assets)
        
        summary = (
            f"📈 *RESUMEN EJECUTIVO*\n"
            f"{'─' * 40}\n"
            f"🎯 Oportunidades detectadas: *{len(top_assets)}*\n"
            f"🟢 Señales MUY FUERTES: *{strong_signals}*\n"
            f"⭐ Score promedio: *{avg_score:.1f}/10*\n"
            f"💎 Ratio R/R promedio: *{avg_rr:.1f}:1*\n\n"
        )
        
        # Análisis detallado de cada activo
        body = f"{'═' * 40}\n*ANÁLISIS DETALLADO*\n{'═' * 40}\n\n"
        
        for i, a in enumerate(top_assets, 1):
            symbol = a.get('symbol', 'N/A')
            score = a.get('score', 0)
            indicator = a.get('indicator', '🔄')
            strength = a.get('strength', 'MEDIA')
            signal = a.get('signal', 'Sin señal')
            
            # Precios
            close = a.get('close', 0)
            entry_opt = a.get('entry_optimal', close)
            entry_max = a.get('entry_max', close)
            stop_loss = a.get('stop_loss', 0)
            target_1 = a.get('target_1', 0)
            target_2 = a.get('target_2', 0)
            target_3 = a.get('target_3', 0)
            
            # Métricas
            rsi = a.get('rsi', 0)
            stoch_k = a.get('stoch_k', 0)
            adx = a.get('adx', 0)
            volume_ratio = a.get('volume_ratio', 1.0)
            atr_pct = a.get('atr_pct', 0)
            trend = a.get('trend', 'lateral')
            
            # Ratios
            risk_pct = a.get('risk_pct', 0)
            rr_1 = a.get('rr_ratio_1', 0)
            rr_2 = a.get('rr_ratio_2', 0)
            rr_3 = a.get('rr_ratio_3', 0)
            reward_1_pct = a.get('reward_1_pct', 0)
            reward_2_pct = a.get('reward_2_pct', 0)
            reward_3_pct = a.get('reward_3_pct', 0)
            
            # MACD
            macd = a.get('macd', 0)
            macd_signal_val = a.get('macd_signal', 0)
            macd_status = "✅ Alcista" if macd > macd_signal_val else "⚠️ Neutral"

            # Emoji de tendencia
            trend_emoji = "📈" if trend == "alcista" else "📉" if trend == "bajista" else "➡️"
            volume_emoji = "🔊" if volume_ratio > 2.0 else "🔉" if volume_ratio > 1.5 else "🔈"

            # Sentiment info
            sentiment = a.get('sentiment', {})
            if sentiment:
                sentiment_score = sentiment.get('score', 0)
                sentiment_label = sentiment.get('label', 'neutral')
                sentiment_emoji = "📰" if sentiment_score > 0 else "📉" if sentiment_score < 0 else "➖"
                sentiment_info = (
                    f"📰 *SENTIMENT:*\n"
                    f"  └─ {sentiment_emoji} {sentiment_label} (score: {sentiment_score:+.1f})\n\n"
                )
            else:
                sentiment_info = ""

            asset_report = (
                f"{indicator} *{i}. {symbol}* - Score: `{score:.1f}/10`\n"
                f"{'─' * 40}\n"
                f"📍 *{signal}* ({strength})\n"
                f"💰 Precio actual: `${close:.2f}`\n\n"
                
                f"🎯 *PLAN DE ENTRADA:*\n"
                f"  ├─ Entrada óptima: `${entry_opt:.2f}`\n"
                f"  ├─ Entrada máxima: `${entry_max:.2f}`\n"
                f"  └─ 💡 *Mejor momento: Lunes apertura*\n\n"
                
                f"🛡️ *GESTIÓN DE RIESGO:*\n"
                f"  └─ Stop Loss: `${stop_loss:.2f}` (-{risk_pct:.1f}%)\n\n"
                
                f"🎁 *OBJETIVOS DE BENEFICIO:*\n"
                f"  ├─ Target 1: `${target_1:.2f}` (+{reward_1_pct:.1f}%) - R/R {rr_1:.1f}:1\n"
                f"  ├─ Target 2: `${target_2:.2f}` (+{reward_2_pct:.1f}%) - R/R {rr_2:.1f}:1 ⭐\n"
                f"  └─ Target 3: `${target_3:.2f}` (+{reward_3_pct:.1f}%) - R/R {rr_3:.1f}:1\n\n"
                
                f"📊 *INDICADORES TÉCNICOS:*\n"
                f"  ├─ RSI(9): `{rsi:.0f}` | Stoch: `{stoch_k:.0f}`\n"
                f"  ├─ ADX: `{adx:.0f}` | ATR: `{atr_pct:.1f}%`\n"
                f"  ├─ {trend_emoji} Tendencia: {trend}\n"
                f"  ├─ MACD: {macd_status}\n"
                f"  └─ {volume_emoji} Volumen: `{volume_ratio:.1f}x`\n\n"
                
                f"{sentiment_info}"
                
                f"💡 *RECOMENDACIÓN:*\n"
                f"  └─ Comprar en zona ${entry_opt:.2f}-${entry_max:.2f}\n"
                f"     Vender 50% en Target 1, 50% en Target 2\n"
                f"     Stop estricto en ${stop_loss:.2f}\n\n"
                f"{'═' * 40}\n\n"
            )
            
            body += asset_report
        
        # Footer
        footer = (
            f"📋 *NOTAS IMPORTANTES:*\n"
            f"• Capital sugerido: €2,500-3,000 por operación\n"
            f"• Máximo 1-2 posiciones simultáneas\n"
            f"• Stop loss obligatorio al 1%\n"
            f"• Timeframe: 3-5 días máximo\n"
            f"• Actualización: Lunes por la mañana\n\n"
            f"_⚠️ Este informe es informativo. No es recomendación de inversión._\n"
        )
        
        return header + summary + body + footer

    def format_update_report(self, top_assets):
        """Informe LUNES: Actualización rápida del estado."""
        now = datetime.datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')
        
        header = (
            f"{'═' * 40}\n"
            f"🔄 *ACTUALIZACIÓN LUNES*\n"
            f"🕐 {now}\n"
            f"{'═' * 40}\n\n"
        )
        
        if not top_assets:
            return header + "✅ No hay cambios significativos. Revisar informe del viernes.\n"
        
        body = ""
        for i, a in enumerate(top_assets, 1):
            symbol = a.get('symbol', 'N/A')
            score = a.get('score', 0)
            indicator = a.get('indicator', '🔄')
            close = a.get('close', 0)
            entry_opt = a.get('entry_optimal', close)
            entry_max = a.get('entry_max', close)
            signal = a.get('signal', 'Sin señal')
            
            # Determinar acción
            if close <= entry_opt * 1.01:
                action = "✅ *ZONA DE COMPRA ACTIVA*"
                detail = f"Entrada óptima: ${entry_opt:.2f}-${entry_max:.2f}"
            elif close <= entry_max:
                action = "🟡 *EN RANGO DE ENTRADA*"
                detail = f"Precio aún válido hasta ${entry_max:.2f}"
            else:
                action = "🔴 *CANCELAR - Ya rebotó*"
                detail = f"Precio superó entrada máxima (+{((close/entry_max-1)*100):.1f}%)"
            
            body += (
                f"{indicator} *{i}. {symbol}* - Score: `{score:.1f}/10`\n"
                f"💰 Precio actual: `${close:.2f}`\n"
                f"{action}\n"
                f"💡 {detail}\n"
                f"📍 {signal}\n\n"
            )
        
        footer = (
            f"{'─' * 40}\n"
            f"💡 *Recomendación del día:*\n"
            f"Revisar valores en 🟢 verde para entradas hoy.\n"
            f"Valores en 🔴 rojo ya no son válidos.\n\n"
            f"_Próxima actualización: Viernes_\n"
        )
        
        return header + body + footer

    def send_report(self, top_assets):
        """Envía el informe según el tipo configurado."""
        if self.report_type == "detailed":
            message = self.format_detailed_report(top_assets)
        else:
            message = self.format_update_report(top_assets)
        
        report = {
            "date": datetime.datetime.utcnow().isoformat(),
            "type": self.report_type,
            "count": len(top_assets),
            "top_assets": top_assets
        }

        if not self.token or not self.chat_id:
            print("⚠️ No se puede enviar a Telegram: credenciales faltantes.")
            print(message)  # Imprimir en consola al menos
            return report

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        # Telegram tiene límite de 4096 caracteres por mensaje
        # Si es muy largo, dividir en varios mensajes
        max_length = 4000
        messages = []
        
        if len(message) <= max_length:
            messages = [message]
        else:
            # Dividir por secciones (cada activo)
            parts = message.split("═" * 40)
            current_msg = parts[0]
            
            for part in parts[1:]:
                if len(current_msg) + len(part) + 40 < max_length:
                    current_msg += "═" * 40 + part
                else:
                    messages.append(current_msg)
                    current_msg = part
            
            if current_msg:
                messages.append(current_msg)
        
        try:
            for i, msg in enumerate(messages):
                payload = {
                    "chat_id": self.chat_id,
                    "text": msg,
                    "parse_mode": "Markdown"
                }
                response = requests.post(url, data=payload, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ Mensaje {i+1}/{len(messages)} enviado correctamente.")
                else:
                    print(f"❌ Error en mensaje {i+1}: {response.status_code} - {response.text}")
                
                # Pequeña pausa entre mensajes
                if i < len(messages) - 1:
                    import time
                    time.sleep(1)
                    
        except Exception as e:
            print(f"⚠️ Error al enviar: {e}")

        return report

    def send_test_message(self, text="✅ Test de conexión correcto."):
        """Envía mensaje de prueba."""
        if not self.token or not self.chat_id:
            print("⚠️ No se puede enviar mensaje de prueba.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": text}
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print("✅ Test exitoso.")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
