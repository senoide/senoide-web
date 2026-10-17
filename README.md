# senoide.es — web pública y puerta de entrada de SENOIDE

Se sirve desde un servidor propio en la UE (Hetzner) con IP dedicada, para no depender de las IP compartidas de Cloudflare (bloqueos de LaLiga en España).

- `site/` — la web estática (lo que ve el cliente).
- `Caddyfile` — servidor web: senoide.es (web), www → senoide.es, app.senoide.es (reenvía a la app en Cloudflare, `origin-app.senoide.es`).
- `scripts/actualizar.sh` — el servidor trae los cambios de este repositorio cada 5 minutos.
- `servidor-cloud-init.yaml` — configuración automática del servidor al crearlo (sin contraseñas ni claves).

Para cambiar la web: editar `site/` y subir a `main`. En 5 minutos está publicado.

## Cómo se genera `site/`
La web se escribe en la carpeta de OneDrive `SENOIDE/web-senoide` (textos en `contenido/`, diseño en `plantillas/`, calculadora en `assets/senoide.js`). `python build.py` genera `publicar/`; su contenido se copia a `site/` (sin tocar `site/assets/fonts`) y se sube a `main`. Ya no se sube nada al Worker de Cloudflare `lucky-fog-e704`.
