#!/usr/bin/env python3
"""
Scheduler para Render.com con Keep-Alive
Mantiene el servicio activo y ejecuta análisis en horarios programados.
"""

import os
import subprocess
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler para health checks de Render"""
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK - Scheduler running')
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
    logger.info(f"✅ Health check server running on port {port}")
    server.serve_forever()


def run_analysis():
    """Ejecuta el análisis de mercado"""
    day = datetime.now().strftime("%A")
    hour = datetime.now().strftime("%H:%M")
    
    logger.info("="*60)
    logger.info(f"🚀 Iniciando análisis de mercado")
    logger.info(f"📅 {day} {hour} UTC")
    logger.info("="*60)
    
    try:
        result = subprocess.run(
            ["python", "orchestrator.py"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos max
        )
        
        # Mostrar output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            logger.info("✅ Análisis completado exitosamente")
        else:
            logger.error("❌ Error en análisis:")
            if result.stderr:
                print(result.stderr)
                
    except subprocess.TimeoutExpired:
        logger.error("⚠️ Timeout: Análisis excedió 30 minutos")
    except Exception as e:
        logger.error(f"❌ Error ejecutando análisis: {e}")
    
    logger.info("="*60)


def keep_alive_ping():
    """
    Keep-alive ping para evitar que Render pause el servicio.
    Se ejecuta cada 10 minutos.
    """
    logger.info("⏰ Keep-alive ping - Servicio activo")


def main():
    """Función principal del scheduler"""
    logger.info("="*60)
    logger.info("🚀 ANALIZADOR FINANCIERO - Scheduler v2")
    logger.info("="*60)
    logger.info("📊 Optimizado para Render.com Free Tier")
    logger.info(f"🕐 Iniciado: {datetime.now()} UTC")
    logger.info("")
    
    # Verificar variables de entorno
    required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️ Variables faltantes: {', '.join(missing_vars)}")
    else:
        logger.info("✅ Variables de entorno configuradas")
    
    finnhub = os.getenv('FINNHUB_API_KEY')
    if not finnhub:
        logger.info("⚠️ Finnhub deshabilitado (opcional)")
    
    logger.info("")
    
    # Iniciar servidor de health checks en thread separado
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Crear scheduler
    scheduler = BackgroundScheduler(timezone='UTC')
    
    # ⏰ KEEP-ALIVE: Ping cada 10 minutos para mantener servicio despierto
    scheduler.add_job(
        func=keep_alive_ping,
        trigger='interval',
        minutes=10,
        id='keep_alive',
        name='Keep Alive Ping',
        max_instances=1
    )
    
    # 📅 ANÁLISIS DIARIO: Lunes-Viernes 09:00 UTC
    scheduler.add_job(
        func=run_analysis,
        trigger=CronTrigger(day_of_week='mon-fri', hour=9, minute=0, timezone='UTC'),
        id='daily_analysis',
        name='Daily Market Analysis',
        max_instances=1
    )
    
    # 📊 INFORME SEMANAL: Viernes 18:00 UTC
    scheduler.add_job(
        func=run_analysis,
        trigger=CronTrigger(day_of_week='fri', hour=18, minute=0, timezone='UTC'),
        id='weekly_report',
        name='Weekly Market Report',
        max_instances=1
    )
    
    # Iniciar scheduler
    scheduler.start()
    
    logger.info("📅 Tareas programadas:")
    logger.info("   • Keep-alive: Cada 10 minutos")
    logger.info("   • Análisis diario: Lun-Vie 09:00 UTC")
    logger.info("   • Informe semanal: Vie 18:00 UTC")
    logger.info("")
    
    # Mostrar próximas ejecuciones
    logger.info("🔜 Próximas ejecuciones:")
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        if next_run:
            logger.info(f"   • {job.name}: {next_run.strftime('%Y-%m-%d %H:%M UTC')}")
    
    logger.info("")
    logger.info("✅ Scheduler activo y en espera")
    logger.info("="*60)
    logger.info("")
    
    # 🔥 EJECUCIÓN INICIAL (para pruebas) - Comentar después de verificar
    logger.info("🔥 Ejecutando análisis inicial (modo test)...")
    run_analysis()
    
    # Mantener el proceso corriendo
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Deteniendo scheduler...")
        scheduler.shutdown()
        logger.info("👋 Scheduler detenido")


if __name__ == "__main__":
    main()
