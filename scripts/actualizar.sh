#!/bin/sh
# Trae los cambios de GitHub y recarga Caddy si cambió su configuración.
set -e
cd /srv/senoide-web
ANTES=$(sha256sum Caddyfile | cut -d' ' -f1)
git fetch -q origin main && git reset -q --hard origin/main
DESPUES=$(sha256sum Caddyfile | cut -d' ' -f1)
if [ "$ANTES" != "$DESPUES" ]; then
  caddy validate --config /srv/senoide-web/Caddyfile --adapter caddyfile && systemctl reload caddy
fi
