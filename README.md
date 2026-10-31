# senoide.es — web pública y puerta de entrada de SENOIDE

Se sirve desde un servidor propio en la UE (UpCloud, Madrid) con IP dedicada, para no depender de las IP compartidas de Cloudflare (bloqueos de LaLiga en España).

- `fuente/` — el código de la web: textos (`contenido/`), diseño (`plantillas/`), estilos, calculadora y fuentes (`assets/`), fotos (`fotos/`) y el generador `build.py`.
- `site/` — la web generada (lo que ve el cliente). No se edita a mano: se regenera desde `fuente/`.
- `Caddyfile` — servidor web: senoide.es (web), www → senoide.es, app.senoide.es (reenvía a la app en Cloudflare, `origin-app.senoide.es`) y pruebas.senoide.es (reenvía al entorno de pruebas, `origin-pruebas.senoide.es`).
- `scripts/actualizar.sh` — el servidor trae los cambios de este repositorio cada 5 minutos.
- `servidor-cloud-init.yaml` — configuración automática del servidor al crearlo (sin contraseñas ni claves).

Para cambiar la web: editar `fuente/` y subir a `main`. GitHub genera `site/` solo (`.github/workflows/web.yml`) y el servidor lo publica en unos 5 minutos.

## Cómo se genera `site/`
Desde el 18/10/2026 el código vive solo en este repositorio (antes estaba en la carpeta de OneDrive `SENOIDE/web-senoide`, que ya no se usa).

- Textos: `fuente/contenido/` (servicios, consejos, noticias, trabajos y legal), en Markdown sencillo con cabecera entre `---`.
- Diseño: `fuente/plantillas/` (`base.html` = cabecera, menú y pie de todas las páginas; `inicio.html` = portada; `mantenimiento.html` = planes).
- Datos de la empresa: bloque `CONFIG` al principio de `fuente/build.py`.
- Calculadora y precios: `fuente/assets/senoide.js`.

Al subir un cambio de `fuente/` a `main`, la acción «Generar web» ejecuta `build.py` y sube el `site/` nuevo. También se puede generar a mano: `cd fuente && python build.py` (o `python build.py --ver` para verla en http://localhost:8000).
