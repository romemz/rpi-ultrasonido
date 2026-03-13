# Configurar Telegram Bot – Medidor UTC

## Paso 1 — Crear el bot (1 minuto)
1. Abre Telegram y busca **@BotFather**
2. Escribe `/newbot`
3. Ponle un nombre: `Medidor UTC`
4. Ponle un usuario: `medidor_utc_bot` (debe terminar en _bot)
5. BotFather te dará un **TOKEN** → cópialo

## Paso 2 — Obtener tu Chat ID
1. Busca tu bot en Telegram: `@medidor_utc_bot`
2. Presiona **START** y manda cualquier mensaje (ej: "hola")
3. Abre en el navegador (reemplaza TU_TOKEN):
   `https://api.telegram.org/botTU_TOKEN/getUpdates`
4. Busca el campo `"id"` dentro de `"chat"` → ese es tu **CHAT_ID**

## Paso 3 — Configurar monitoreo.py
Abre `/var/www/html/rpi-ultrasonido/python/monitoreo.py` y edita:

```python
TELEGRAM_TOKEN   = 'TU_TOKEN_AQUI'
TELEGRAM_CHAT_ID = 'TU_CHAT_ID_AQUI'
```

## Para notificar a varias personas o un grupo:
```python
TELEGRAM_CHAT_ID = ['111111111', '222222222']   # varios usuarios
# o
TELEGRAM_CHAT_ID = '-1001234567890'              # ID de un grupo
```

## Para añadir a un grupo:
1. Crea un grupo en Telegram
2. Agrega tu bot al grupo
3. Manda un mensaje en el grupo
4. Visita getUpdates y copia el id del grupo (empieza con -)

## Paso 4 — Probar manualmente
```bash
sudo python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py
```

## Paso 5 — Cron (medir cada 5 minutos)
```bash
sudo crontab -e
```
Agrega:
```
*/5 * * * * /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py >> /var/log/tinaco_monitoreo.log 2>&1
```

## Cuándo llegan las notificaciones
- ⚠️  Tinaco al **50%** → primera vez que baja a ese nivel
- 🚨  Tinaco al **25%** → primera vez que baja a ese nivel  
- 🚫  Tinaco al **0%**  → primera vez que llega a vacío
- Los umbrales se **resetean automáticamente** cuando el tinaco se llena de nuevo (>55%)
