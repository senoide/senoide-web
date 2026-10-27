#!/bin/sh
# Trae los cambios de GitHub y recarga Caddy si cambió su configuración.
#
# 27/10/2026 · MIGRACIÓN DE SEGURIDAD (se ejecuta una sola vez):
# hasta hoy el servidor ejecutaba como root este archivo del repositorio, así que cualquiera que pudiera
# subir algo a GitHub controlaba el servidor. En la primera ejecución este script instala una copia fija en
# /usr/local/sbin/senoide-actualizar.sh, cambia la tarea programada para que use esa copia y deja un informe
# del estado del servidor en https://senoide.es/estado-servidor.txt (se borra solo a los 60 minutos).
# A partir de ahí, este archivo del repositorio queda solo como documentación.
set -e
cd /srv/senoide-web
ANTES=$(sha256sum Caddyfile | cut -d' ' -f1)
git fetch -q origin main && git reset -q --hard origin/main
DESPUES=$(sha256sum Caddyfile | cut -d' ' -f1)
if [ "$ANTES" != "$DESPUES" ]; then
  caddy validate --config /srv/senoide-web/Caddyfile --adapter caddyfile && systemctl reload caddy
fi

# ---------- migración única ----------
set +e
DEST=/usr/local/sbin/senoide-actualizar.sh
ORIG=/srv/senoide-web/scripts/actualizar.sh
[ "$(readlink -f "$0")" = "$DEST" ] && exit 0

cat > "$DEST.tmp" <<'FIN'
#!/bin/sh
# Actualización de la web de SENOIDE desde GitHub (copia fija en el servidor, instalada el 27/10/2026).
# Este archivo NO se actualiza desde el repositorio: lo que se suba a GitHub no se ejecuta como root.
# Para cambiarlo hay que hacerlo en el propio servidor.
set -e
cd /srv/senoide-web
ANTES=$(sha256sum Caddyfile | cut -d' ' -f1)
git fetch -q origin main && git reset -q --hard origin/main
DESPUES=$(sha256sum Caddyfile | cut -d' ' -f1)
if [ "$ANTES" != "$DESPUES" ]; then
  caddy validate --config /srv/senoide-web/Caddyfile --adapter caddyfile && systemctl reload caddy
fi
# el informe de estado de la migración se borra solo a los 60 minutos
find /srv/senoide-web/site -maxdepth 1 -name estado-servidor.txt -mmin +60 -delete 2>/dev/null || true
FIN
chown root:root "$DEST.tmp" && chmod 700 "$DEST.tmp" && mv "$DEST.tmp" "$DEST"

CAMBIOS=""
for f in /etc/cron.d/*; do
  if [ -f "$f" ] && grep -q "$ORIG" "$f"; then sed -i "s#$ORIG#$DEST#g" "$f" && CAMBIOS="$CAMBIOS $f"; fi
done
if crontab -l 2>/dev/null | grep -q "$ORIG"; then
  crontab -l | sed "s#$ORIG#$DEST#g" | crontab - && CAMBIOS="$CAMBIOS crontab-root"
fi
TIMERS=$(grep -rl "$ORIG" /etc/systemd/system 2>/dev/null | tr '\n' ' ')

S=/srv/senoide-web/site/estado-servidor.txt
{
  echo "Informe de estado del servidor · $(date -u '+%Y-%m-%d %H:%M UTC')"
  echo "Sistema: $(. /etc/os-release 2>/dev/null; echo "$PRETTY_NAME") · núcleo $(uname -r)"
  echo
  echo "== Migración del script de actualización"
  echo "Copia fija instalada: $( [ -x "$DEST" ] && echo sí || echo NO )"
  echo "Tareas cambiadas a la copia fija:${CAMBIOS:- NINGUNA}"
  echo "Otras referencias al script del repositorio (systemd): ${TIMERS:-ninguna}"
  echo "Referencias que quedan al script del repositorio en cron: $(grep -l "$ORIG" /etc/cron.d/* 2>/dev/null | tr '\n' ' ')$(crontab -l 2>/dev/null | grep -c "$ORIG") (debe ser 0)"
  echo
  echo "== Cortafuegos (ufw)"
  ufw status 2>&1
  echo
  echo "== Acceso remoto SSH"
  echo "Arranque automático: $(systemctl is-enabled ssh 2>&1) · En marcha: $(systemctl is-active ssh 2>&1)"
  echo
  echo "== Puertos escuchando (TCP)"
  ss -ltnH 2>/dev/null | awk '{print $4}' | sed 's/.*://' | sort -un | tr '\n' ' '
  echo
  echo
  echo "== Actualizaciones automáticas"
  echo "Servicio: $(systemctl is-active unattended-upgrades 2>&1)"
  grep -h "Unattended-Upgrade\|Automatic-Reboot" /etc/apt/apt.conf.d/20auto-upgrades /etc/apt/apt.conf.d/51senoide-reinicio 2>/dev/null
  echo "Reinicio pendiente: $( [ -f /var/run/reboot-required ] && echo sí || echo no )"
  echo "Última ejecución: $(ls -l --time-style=+%Y-%m-%d /var/log/unattended-upgrades/unattended-upgrades.log 2>/dev/null | awk '{print $6}')"
  echo
  echo "== Caddy"
  echo "En marcha: $(systemctl is-active caddy 2>&1) · $(caddy version 2>/dev/null | cut -d' ' -f1)"
  echo "Llave ORIGIN_SECRET configurada: $( [ -f /etc/systemd/system/caddy.service.d/secreto.conf ] && echo sí || echo no )"
} > "$S" 2>&1
chmod 644 "$S"
exit 0
