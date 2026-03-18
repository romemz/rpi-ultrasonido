# Configuración del Cron — Medidor Inteligente UTC

## Cron cada 1 minuto (para exposición)

```bash
sudo crontab -e
```

Agrega esta línea (reemplaza la anterior si tenías de 5 min):

```
* * * * * /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py >> /var/log/tinaco_monitoreo.log 2>&1
```

> `* * * * *` = cada 1 minuto

---

## Cron cada 5 minutos (uso normal)

Si después de la exposición quieres volver al intervalo normal:

```
*/5 * * * * /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py >> /var/log/tinaco_monitoreo.log 2>&1
```

---

## Verificar que el cron está activo

```bash
sudo crontab -l
```

## Ver el log en tiempo real

```bash
tail -f /var/log/tinaco_monitoreo.log
```

## Verificar estado generado

```bash
cat /var/www/html/rpi-ultrasonido/estado_tinaco.json
```

---

## Cómo funcionan las notificaciones Telegram

- El cron ejecuta `monitoreo.py` cada 1 minuto
- `monitoreo.py` llama a `medidor_db.py` que mide con el sensor
- Guarda en MariaDB y escribe `estado_tinaco.json`
- Solo envía Telegram cuando el nivel **CAMBIA** de rango:
  - ⚠️  Cruza a **50%** o menos → "Tinaco a la mitad"
  - 🚨  Cruza a **25%** o menos → "Nivel bajo de agua"
  - 🚫  Llega a **0%**          → "Tinaco SIN AGUA"
- Si el nivel sube a **51% o más** → las alertas se reinician
- **No manda duplicados** si permanece en el mismo rango
