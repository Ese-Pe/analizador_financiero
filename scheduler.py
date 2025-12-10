#!/usr/bin/env python3
"""
Scheduler para Render.com
Mantiene el servicio activo y ejecuta análisis en horarios programados.
"""

import schedule
import time
import subprocess
from datetime import datetime
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler para health checks de Render"""
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Silenciar logs de health checks
        pass

def start_health_server():
    """Inicia servidor HTTP para health checks de Render"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"✅ Health check server running on port {port}")
    server.serve_forever()

def run_analysis():
    """Ejecuta el análisis de mercado"""
    day = datetime.utcnow().strftime("%A")
    hour = datetime.utcnow().strftime("%H:%M")
    print(f"\n{'='*60}")
    print(f"🚀 [{datetime.utcnow()}] Iniciando análisis")
    print(f"📅 {day} {hour} UTC")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            ["python", "orchestrator.py"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos max
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"\n✅ Análisis completado exitosamente")
        else:
            print(f"\n❌ Error en análisis:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout: Análisis excedió 30 minutos")
    except Exception as e:
        print(f"❌ Error ejecutando análisis: {e}")
    
    print(f"{'='*60}\n")

def main():
    """Función principal del scheduler"""
    print("="*60)
    print("🚀 ANALIZADOR FINANCIERO - Scheduler")
    print("="*60)
    print("📊 Optimizado para Render.com")
    print(f"🕐 Servidor iniciado: {datetime.utcnow()} UTC")
    print()
    print("📅 Horario de ejecuciones:")
    print("   • Lunes-Viernes: 09:00 UTC (Análisis diario)")
    print("   • Viernes: 18:00 UTC (Informe semanal)")
    print("="*60)
    print()
    
    # Verificar variables de entorno
    required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'FINNHUB_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  ADVERTENCIA: Variables faltantes: {', '.join(missing_vars)}")
    else:
        print("✅ Todas las variables de entorno configuradas")
    
    print()
    
    # Iniciar servidor de health checks en thread separado
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Programar tareas
    schedule.every().monday.at("09:00").do(run_analysis)
    schedule.every().tuesday.at("09:00").do(run_analysis)
    schedule.every().wednesday.at("09:00").do(run_analysis)
    schedule.every().thursday.at("09:00").do(run_analysis)
    schedule.every().friday.at("09:00").do(run_analysis)
    schedule.every().friday.at("18:00").do(run_analysis)
    
    print("✅ Scheduler configurado correctamente")
    print("⏰ Esperando próxima ejecución programada...")
    print()
    
    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
