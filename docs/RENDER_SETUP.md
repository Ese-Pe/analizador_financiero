# 🚀 Guía de Deploy en Render.com

## ¿Por qué Render?

- ✅ **750 horas gratis/mes** (suficiente para uso 24/7)
- ✅ **Auto-deploy** desde GitHub
- ✅ **Sin tarjeta de crédito** requerida
- ✅ **Fácil configuración** (5 minutos)
- ✅ **Logs en tiempo real**
- ✅ **Health checks automáticos**

---

## 🏁 Setup Completo (5 minutos)

### 1. Crear cuenta en Render

1. Ve a: https://render.com
2. Click **"Get Started"**
3. Sign up con GitHub (recomendado)
4. Autoriza Render a acceder a tus repos

### 2. Crear Web Service

1. Dashboard → **"New +"** → **"Web Service"**
2. **"Connect a repository"**
3. Selecciona: `analizador_financiero`
4. Click **"Connect"**

### 3. Configurar el servicio

Render detecta automáticamente que es Python, pero verifica:

#### **Básico:**
- **Name**: `analizador-financiero`
- **Region**: Frankfurt (más cerca de Europa)
- **Branch**: `main`
- **Runtime**: Python 3

#### **Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python scheduler.py`

#### **Plan:**
- Selecciona: **Free** ✅

### 4. Variables de entorno

En la sección **"Environment"** → **"Add Environment Variable"**:

```
TELEGRAM_TOKEN
Value: tu_token_del_bot

TELEGRAM_CHAT_ID  
Value: tu_chat_id

FINNHUB_API_KEY
Value: tu_finnhub_key
```

Click **"Add"** para cada una.

### 5. Deploy

Click **"Create Web Service"**

Render empezará a:
1. Clonar tu repo
2. Instalar dependencias
3. Iniciar `scheduler.py`

**Tiempo estimado**: 2-3 minutos

---

## ✅ Verificar que funciona

### Ver logs en tiempo real:

1. Dashboard → Tu servicio
2. Tab **"Logs"**
3. Deberías ver:

```
🚀 ANALIZADOR FINANCIERO - Scheduler
════════════════════════════════════
📅 Horario de ejecuciones:
   • Lunes-Viernes: 09:00 UTC
   • Viernes: 18:00 UTC
✅ Health check server running on port 10000
✅ Scheduler configurado correctamente
⏰ Esperando próxima ejecución programada...
```

### Health check:

Render hace pings automáticos a `/health` cada 30 segundos.

Si todo está bien, verás:
- **Status**: `Live` (verde)
- **Health**: Healthy

---

## 🔄 Actualizar código

Súper fácil:

```bash
# Local
git add .
git commit -m "Update analysis parameters"
git push origin main

# Render detecta el push
# → Auto-redeploy en 2-3 minutos ✅
```

Logs en tiempo real durante el deploy.

---

## ⚙️ Configuración Avanzada

### Cambiar horarios de ejecución

Editar `scheduler.py`:

```python
# Cambiar hora (UTC)
schedule.every().monday.at("10:00").do(run_analysis)  # 10:00 en vez de 09:00
```

Commit + push → Redeploy automático.

### Ejecutar manualmente

Opción 1 - Desde Render Shell:
1. Dashboard → **"Shell"** tab
2. `python orchestrator.py`

Opción 2 - Trigger via webhook (opcional):
1. Settings → **"Deploy Hook"**
2. Copy URL
3. `curl -X POST tu_webhook_url`

---

## 💰 Monitorear uso

Dashboard → **"Metrics"**

Verás:
- CPU usage
- Memory usage
- Bandwidth
- Horas consumidas

**Tu caso estimado:**
- Script activo 24/7
- CPU casi en idle (solo ejecuta 2x/día)
- ~730 horas/mes
- **Dentro del free tier** ✅

---

## 🐛 Troubleshooting

### Service no arranca

**Ver logs**: Tab "Logs" para ver el error

**Errores comunes:**

1. **ModuleNotFoundError**
   ```
   Solución: Verificar requirements.txt
   ```

2. **Port binding error**
   ```
   Solución: scheduler.py ya maneja PORT env var
   ```

3. **Variables de entorno faltantes**
   ```
   Solución: Añadir en Environment tab
   ```

### Service se cae (crashes)

Render automáticamente lo reinicia.

Ver logs para identificar causa:
- Timeout en análisis (>30min)
- Memory limit exceeded
- API rate limit

### Script no ejecuta en horario

Verificar:
1. Timezone = UTC (Render usa UTC)
2. Logs: ¿Se programó correctamente?
3. Health check OK

---

## 📊 Logs útiles

### Ver últimos logs:

Dashboard → Logs → Últimos 100 logs

### Buscar errores:

Logs → Search: `ERROR` o `❌`

### Logs de ejecución:

```
[2024-11-12 09:00:00] 🚀 Iniciando análisis
...
✅ Análisis completado exitosamente
```

---

## 🔒 Seguridad

### Variables de entorno

- ✅ Nunca commitear `.env` al repo
- ✅ Usar Environment Variables en Render
- ✅ Rotar tokens periódicamente

### Secrets rotation

1. Generar nuevo token
2. Render → Environment → Edit variable
3. Update value
4. Deploy se reinicia automáticamente

---

## 🆚 Render vs otras opciones

| Feature | Render | Railway | PythonAnywhere |
|---------|--------|---------|----------------|
| **Horas gratis** | 750h/mes | $5 crédito | 1 cron/día |
| **Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Auto-deploy** | ✅ | ✅ | ❌ Manual |
| **Health checks** | ✅ Auto | ✅ Auto | ❌ |
| **Logs** | ✅ Real-time | ✅ Real-time | ⚠️ Limited |
| **Free tier** | ✅ Genoroso | ⚠️ $5/mes | ✅ Limitado |

**Para tu caso:** Render es perfecto. 🏆

---

## 💡 Tips

### Optimizar cold starts

Render free tier "duerme" después de 15min inactividad.

**Solución:** Health check server mantiene servicio activo.

### Múltiples environments

```bash
# Crear branch staging
git checkout -b staging
git push origin staging

# En Render, crear nuevo servicio apuntando a branch staging
```

### Backup de datos

Render no tiene almacenamiento persistente en free tier.

Para guardar reportes:
- Enviar a Telegram (ya lo hace)
- O integrar con Google Drive/Dropbox

---

## 📞 Soporte

- **Docs**: https://render.com/docs
- **Community**: https://community.render.com
- **Status**: https://status.render.com

---

## ✅ Checklist Post-Deploy

- [ ] Servicio **Status: Live** (verde)
- [ ] Logs muestran scheduler activo
- [ ] Health check respondiendo
- [ ] Variables de entorno configuradas
- [ ] Test manual ejecutado con éxito
- [ ] Telegram bot recibiendo mensajes
- [ ] Auto-deploy funcionando (test con commit)

---

**🎉 ¡Listo! Tu analizador financiero está en producción.**

Próxima ejecución: Lunes 09:00 UTC ⏰
