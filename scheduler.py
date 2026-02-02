#!/usr/bin/env python3
"""
Scheduler para Render.com con Keep-Alive
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
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
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
        pass


def start_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"✅ Health check server on port {port}")
    server.serve_forever()


def run_analysis():
    day = datetime.now().strftime("%A")
    hour = datetime.now().strftime("%H:%M")
    
    logger.info("="*60)
    logger.info(f"🚀 Iniciando análisis - {day} {hour} UTC")
    logger.info("="*60)
    
    try:
        result = subprocess.run(
            ["python", "orchestrator.py"],
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            logger.info("✅ Análisis completado")
        else:
            logger.error("❌ Error en análisis")
            if result.stderr:
                print(result.stderr)
                
    except subprocess.TimeoutExpired:
        logger.error("⚠️ Timeout")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    
    logger.info("="*60)


def keep_alive_ping():
    """Mantiene el servicio activo haciendo ping al propio endpoint de health."""
    port = int(os.environ.get('PORT', 10000))
    url = f"http://localhost:{port}/health"

    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            logger.info(f"⏰ Keep-alive ping OK (status: {status})")
    except urllib.error.URLError as e:
        logger.warning(f"⏰ Keep-alive ping fallido: {e}")
    except Exception as e:
        logger.warning(f"⏰ Keep-alive ping error: {e}")


def main():
    logger.info("="*60)
    logger.info("🚀 ANALIZADOR FINANCIERO - Scheduler v2")
    logger.info("="*60)
    logger.info(f"🕐 Iniciado: {datetime.now()} UTC")
    logger.info("")
    
    required_vars = ['TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️ Variables faltantes: {', '.join(missing_vars)}")
    else:
        logger.info("✅ Variables configuradas")
    
    finnhub = os.getenv('FINNHUB_API_KEY')
    if not finnhub:
        logger.info("⚠️ Finnhub deshabilitado")
    
    logger.info("")
    
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    scheduler = BackgroundScheduler(timezone='UTC')
    
    scheduler.add_job(
        func=keep_alive_ping,
        trigger='interval',
        minutes=10,
        id='keep_alive',
        name='Keep Alive',
        max_instances=1
    )
    
    scheduler.add_job(
        func=run_analysis,
        trigger=CronTrigger(day_of_week='mon-fri', hour=9, minute=0, timezone='UTC'),
        id='daily_analysis',
        name='Daily Analysis',
        max_instances=1
    )
    
    scheduler.add_job(
        func=run_analysis,
        trigger=CronTrigger(day_of_week='fri', hour=18, minute=0, timezone='UTC'),
        id='weekly_report',
        name='Weekly Report',
        max_instances=1
    )
    
    scheduler.start()
    
    logger.info("📅 Tareas programadas:")
    logger.info("   • Keep-alive: Cada 10 min")
    logger.info("   • Análisis diario: Lun-Vie 09:00 UTC")
    logger.info("   • Informe semanal: Vie 18:00 UTC")
    logger.info("")
    
    logger.info("🔜 Próximas ejecuciones:")
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        if next_run:
            logger.info(f"   • {job.name}: {next_run.strftime('%Y-%m-%d %H:%M UTC')}")
    
    logger.info("")
    logger.info("✅ Scheduler activo")
    logger.info("="*60)
    logger.info("")
    
    logger.info("🔥 Ejecutando análisis inicial...")
    run_analysis()
    
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Deteniendo scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
