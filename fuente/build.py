#!/usr/bin/env python3
"""
Generador de la web de SENOIDE.

Uso (desde la carpeta fuente/ del repositorio senoide/senoide-web):
    python build.py            -> genera la web en la carpeta "site/" del repositorio
    python build.py --ver      -> genera y abre un servidor local en http://localhost:8000

Al subir cambios de fuente/ a GitHub, la web se genera sola (.github/workflows/web.yml)
y el servidor la publica en unos 5 minutos.

Para añadir contenido no hace falta tocar este fichero:
    contenido/trabajos/*.md    -> un fichero por trabajo realizado
    contenido/consejos/*.md    -> un fichero por artículo de consejos o normativa
    contenido/servicios/*.md   -> páginas de servicio
    fotos/                     -> las fotos que usan los trabajos y artículos

Solo usa la librería estándar de Python. Si tienes Pillow instalado
(pip install pillow), además reduce las fotos a 1600 px para que la web cargue rápido.
"""
import datetime as dt
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

# ============ DATOS DE LA EMPRESA: revisa y completa ============
CONFIG = {
    "DOMINIO": "https://senoide.es",          # sin barra final; cámbialo si el dominio es otro
    "TITULAR": "Luis M. Sierra Mena",
    "NIF": "46927518C",                  # obligatorio por la LSSI
    "DOMICILIO": "C/ Moncayo, 28, 12594 Oropesa del Mar (Castellón)",
    "TELEFONO": "621 018 374",
    "WHATSAPP": "34621018374",                 # con prefijo 34, sin espacios ni +
    "EMAIL": "info@senoide.es",    # cámbialo por info@tudominio cuando exista
    "CERTIFICADO": "CIBTB-04551",
    "RII": "10-B-D00-12064193",              # Registro Integrado Industrial: empresa instaladora BT, categoría básica
    "AVISO": "Abrimos el <b>2 de noviembre de 2026</b> · ya puedes pedir presupuesto",
    # A partir de APERTURA el aviso de arriba cambia solo (lo decide el navegador del visitante)
    "APERTURA": "2026-11-02",
    "AVISO_ABIERTO": "Atendemos de lunes a viernes, de 8 a 18 h · Urgencias: <a href=\"tel:+34621018374\">621 018 374</a>",
    # App de gestión: recibe las solicitudes de la calculadora y publica los trabajos de los partes
    "API": "https://app.senoide.es",
    # Opiniones: enlace «Pedir reseñas» del Perfil de Empresa de Google (https://g.page/r/.../review). Vacío = no se muestra.
    "RESENAS_URL": "https://g.page/r/CcEAwUZu5RxeEBM/review",
    # Enlace a la ficha de Google para leer las opiniones (por ejemplo, el de «Compartir» del perfil). Vacío = no se muestra.
    "PERFIL_GOOGLE": "https://share.google/tdtfLiFDOJaDpnz7n",
    "HORARIO": [("Mo", "Fr", "08:00", "18:00")],
    # Zona de trabajo: una sola lista para la portada, la calculadora y Google.
    # Tramo de desplazamiento: 0 = incluido (Oropesa), 1 = hasta 20 km (+15 €), 2 = de 20 a 40 km (+30 €).
    # Más de 40 km: precio a medida. Si cambias un municipio aquí, cámbialo también en el Perfil de Empresa de Google.
    "ZONA": [("Oropesa del Mar", 0),
             ("Benicàssim", 1), ("Cabanes", 1), ("Torreblanca", 1),
             ("La Pobla Tornesa", 2), ("Benlloc", 2), ("Vilafamés", 2), ("Borriol", 2),
             ("Castelló de la Plana", 2), ("Alcalà de Xivert-Alcossebre", 2), ("Almassora", 2), ("Vila-real", 2)],
    # Cloudflare Web Analytics (sin cookies). Pega aquí el token cuando lo tengas; vacío = sin analítica.
    "CLOUDFLARE_ANALYTICS_TOKEN": "",
    # Enlaces a perfiles (Perfil de Empresa de Google, Instagram...). Ayudan a Google a unir la web con la ficha.
    "PERFILES": ["https://share.google/tdtfLiFDOJaDpnz7n", "https://www.instagram.com/senoide.es"],
}
# ================================================================

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ.parent / "site"   # la web generada; el servidor la publica desde aquí
PLANTILLAS = RAIZ / "plantillas"
VERSION = os.environ.get("WEB_VERSION") or dt.datetime.now().strftime("%Y%m%d%H%M")
try:
    from zoneinfo import ZoneInfo
    HOY = dt.datetime.now(ZoneInfo("Europe/Madrid")).date()   # fecha en España, para «publicar:»
except Exception:
    HOY = dt.date.today()
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


# ---------- utilidades ----------
def esc(t):
    return html.escape(str(t), quote=True)


def fecha_larga(f):
    return f"{f.day} de {MESES[f.month - 1]} de {f.year}"


def slugify(t):
    t = t.lower()
    for a, b in zip("áéíóúüñàèòç", "aeiouunaeoc"):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def leer_md(ruta):
    """Lee un .md con cabecera entre --- y devuelve (datos, cuerpo)."""
    texto = ruta.read_text(encoding="utf-8")
    datos = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", texto, re.S)
    if m:
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                datos[k.strip().lower()] = v.strip()
        cuerpo = m.group(2)
    else:
        cuerpo = texto
    datos.setdefault("slug", slugify(datos.get("titulo", ruta.stem)) or ruta.stem)
    f = datos.get("fecha", "")
    try:
        datos["_fecha"] = dt.date.fromisoformat(f)
    except ValueError:
        datos["_fecha"] = dt.date.fromtimestamp(ruta.stat().st_mtime)
    datos["_borrador"] = datos.get("borrador", "no").lower() in ("si", "sí", "yes", "true")
    # publicar: AAAA-MM-DD -> hasta ese día la página existe (para revisarla con el enlace),
    # pero no sale en listados, portada, sitemap ni Google. Ese día aparece sola.
    try:
        datos["_publicar"] = dt.date.fromisoformat(datos.get("publicar", ""))
    except ValueError:
        datos["_publicar"] = None
    datos["_oculto"] = bool(datos["_publicar"] and datos["_publicar"] > HOY)
    if datos["_publicar"] and "fecha" not in datos:
        datos["_fecha"] = datos["_publicar"]
    return datos, cuerpo


def inline(t):
    t = esc(t).replace("\\*", "&#42;")  # \* = asterisco literal
    t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f'<img src="{ruta_foto(m.group(2))}" alt="{m.group(1)}" loading="lazy">', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: enlace(m.group(1), m.group(2)), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<em>\1</em>", t)
    return t


def enlace(texto, url):
    externo = url.startswith("http") and not url.startswith(CONFIG["DOMINIO"])
    extra = ' target="_blank" rel="noopener"' if externo else ""
    return f'<a href="{url}"{extra}>{texto}</a>'


def ruta_foto(nombre):
    nombre = nombre.strip()
    if nombre.startswith(("http", "/")):
        return nombre
    return "/fotos/" + nombre


PUBLICADAS = None   # rutas publicadas (se rellena al construir); None = mostrar todo


def condicionales(md):
    """{{si:/trabajos/slug/}}texto{{/si}} -> el texto solo aparece si esa ruta ya está publicada."""
    def f(m):
        ruta = m.group(1).strip()
        return m.group(2) if PUBLICADAS is None or ruta in PUBLICADAS else ""
    return re.sub(r"\{\{si:([^}]+)\}\}(.*?)\{\{/si\}\}", f, md, flags=re.S)


def markdown(md):
    """Markdown sencillo: ## títulos, párrafos, listas, **negrita**, *cursiva*, [enlaces](url), ![fotos](x.jpg)."""
    md = condicionales(md)
    out, lista, parrafo = [], None, []

    def cerrar_parrafo():
        if parrafo:
            out.append("<p>" + inline(" ".join(parrafo)) + "</p>")
            parrafo.clear()

    def cerrar_lista():
        nonlocal lista
        if lista:
            out.append(f"</{lista}>")
            lista = None

    for linea in md.splitlines():
        s = linea.strip()
        if not s:
            cerrar_parrafo(); cerrar_lista(); continue
        if s.startswith(">"):
            cerrar_parrafo(); cerrar_lista()
            out.append('<p class="src">' + inline(s.lstrip("> ")) + "</p>"); continue
        h = re.match(r"^(#{2,3})\s+(.*)", s)
        if h:
            cerrar_parrafo(); cerrar_lista()
            n = len(h.group(1)); a = re.match(r"^(.*?)\s*\{#([\w-]+)\}$", h.group(2))
            out.append(f'<h{n} id="{a.group(2)}">{inline(a.group(1))}</h{n}>' if a else f"<h{n}>{inline(h.group(2))}</h{n}>"); continue
        li = re.match(r"^([-*]|\d+\.)\s+(.*)", s)
        if li:
            cerrar_parrafo()
            tipo = "ol" if li.group(1)[0].isdigit() else "ul"
            if lista != tipo:
                cerrar_lista(); out.append(f"<{tipo}>"); lista = tipo
            out.append("<li>" + inline(li.group(2)) + "</li>"); continue
        cerrar_lista(); parrafo.append(s)
    cerrar_parrafo(); cerrar_lista()
    return "\n".join(out)


# ---------- datos estructurados (schema.org) ----------
def jsonld_empresa():
    d = CONFIG
    org = {
        "@context": "https://schema.org",
        "@type": "Electrician",
        "@id": d["DOMINIO"] + "/#empresa",
        "name": "SENOIDE",
        "description": "Instalaciones eléctricas, averías, boletines, puntos de recarga, fontanería y remates de albañilería.",
        "url": d["DOMINIO"] + "/",
        "logo": d["DOMINIO"] + "/assets/icono-512.png",
        "image": d["DOMINIO"] + "/assets/og-senoide.jpg",
        "telephone": "+" + d["WHATSAPP"],
        "email": d["EMAIL"],
        "founder": {"@type": "Person", "name": d["TITULAR"]},
        "address": {"@type": "PostalAddress", "addressLocality": "Oropesa del Mar",
                    "postalCode": "12594", "addressRegion": "Castellón", "addressCountry": "ES"},
        "areaServed": [{"@type": "City", "name": m} for m, _z in d["ZONA"]],
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification",
             "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
             "opens": h[2], "closes": h[3]} for h in d["HORARIO"]],
        "priceRange": "€€",
    }
    if d["PERFILES"]:
        org["sameAs"] = d["PERFILES"]
    return org


# ---------- montaje de páginas ----------
BASE = (PLANTILLAS / "base.html").read_text(encoding="utf-8")


def pagina(ruta_url, titulo, descripcion, contenido, jsonld=None, og_tipo="website",
           imagen=None, indexar=True):
    d = CONFIG
    url = d["DOMINIO"] + ruta_url
    grafo = [jsonld_empresa()] + ([jsonld] if jsonld else [])
    analitica = ""
    if d["CLOUDFLARE_ANALYTICS_TOKEN"]:
        analitica = ('<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
                     f"data-cf-beacon='{{\"token\": \"{d['CLOUDFLARE_ANALYTICS_TOKEN']}\"}}'></script>")
    rep = {
        "TITULO": esc(titulo), "DESCRIPCION": esc(descripcion), "URL": url,
        "ROBOTS": "index,follow" if indexar else "noindex,follow",
        "OG_TIPO": og_tipo, "IMAGEN": imagen or d["DOMINIO"] + "/assets/og-senoide.jpg",
        "JSONLD": json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False).replace("</", "<\\/"),
        "WHATSAPP": d["WHATSAPP"], "AVISO": d["AVISO"], "TITULAR": esc(d["TITULAR"]), "NIF": esc(d["NIF"]),
        "TELEFONO": d["TELEFONO"], "EMAIL": d["EMAIL"], "TELEFONO_SIN_ESPACIOS": d["TELEFONO"].replace(" ", ""), "VERSION": VERSION, "ANALITICA": analitica,
        "API": d["API"], "APERTURA": d["APERTURA"], "AVISO_ABIERTO": esc(d["AVISO_ABIERTO"]),
        "PIE_OPINIONES": (f' · <a href="{esc(d["PERFIL_GOOGLE"] or d["RESENAS_URL"])}" target="_blank" rel="noopener">SENOIDE en Google</a>'
                          if (d["PERFIL_GOOGLE"] or d["RESENAS_URL"]) else ""),
        "CONTENIDO": contenido,
    }
    out = BASE
    for k, v in rep.items():
        out = out.replace("{{" + k + "}}", v)
    destino = SALIDA / ruta_url.strip("/") / "index.html" if ruta_url != "/" else SALIDA / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(out, encoding="utf-8")
    if indexar:
        SITEMAP.append(url)


def cabecera(eyebrow, titulo, lead="", migas=None):
    m = ""
    if migas:
        m = '<nav class="crumbs" aria-label="Estás en">' + " / ".join(
            f'<a href="{u}">{esc(t)}</a>' if u else esc(t) for t, u in migas) + "</nav>"
    return (f'<section class="page-head"><div class="wrap">{m}'
            f'<p class="eyebrow" style="margin-top:14px">{esc(eyebrow)}</p><h1>{esc(titulo)}</h1>'
            + (f'<p class="lead">{esc(lead)}</p>' if lead else "") + "</div></section>")


def bloque_cta():
    return ('<div class="cta-box"><div><p class="eyebrow" style="color:inherit;opacity:.7">¿Necesitas algo parecido?</p>'
            '<h3 style="margin-top:6px">Calcula un precio orientativo en un minuto.</h3></div>'
            '<a class="btn primary" href="/#presupuesto">Calcular presupuesto</a></div>')


def tarjeta(item, base_url, meta):
    img = ""
    if item.get("portada"):
        img = f'<img src="{ruta_foto(item["portada"])}" alt="{esc(item.get("titulo", ""))}" loading="lazy" width="800" height="600">'
    return (f'<a class="card" href="{base_url}{item["slug"]}/">{img}<div class="body">'
            f'<span class="meta">{esc(meta)}</span><h3>{esc(item.get("titulo", ""))}</h3>'
            f'<p>{esc(item.get("resumen", ""))}</p></div></a>')


def cargar(carpeta):
    items = []
    for f in sorted((RAIZ / "contenido" / carpeta).glob("*.md")):
        if f.name.startswith("_"):
            continue  # las plantillas empiezan por _
        datos, cuerpo = leer_md(f)
        if datos["_borrador"]:
            print(f"  · borrador, no se publica: {f.name}")
            continue
        if datos["_oculto"]:
            print(f"  · oculto hasta el {datos['_publicar'].isoformat()} (solo con enlace): /{carpeta}/{datos['slug']}/")
        datos["_cuerpo"] = cuerpo
        items.append(datos)
    return sorted(items, key=lambda x: x["_fecha"], reverse=True)


def fotos_usadas():
    """Fotos de los artículos que no son borrador (los ocultos sí, para poder revisarlos con el enlace)."""
    usadas = set()
    for carpeta in ("trabajos", "consejos", "noticias", "servicios"):
        d = RAIZ / "contenido" / carpeta
        if not d.exists():
            continue
        for f in d.glob("*.md"):
            if f.name.startswith("_"):
                continue
            datos, cuerpo = leer_md(f)
            if datos["_borrador"]:
                continue
            nombres = [datos.get("portada", "")] + datos.get("fotos", "").split(",")
            nombres += re.findall(r"!\[[^\]]*\]\(([^)]+)\)", cuerpo)
            usadas |= {x.strip() for x in nombres if x.strip() and not x.strip().startswith(("http", "/"))}
    return usadas


def copiar_fotos():
    origen, destino = RAIZ / "fotos", SALIDA / "fotos"
    destino.mkdir(parents=True, exist_ok=True)
    usadas = fotos_usadas()
    try:
        from PIL import Image, ImageOps
    except ImportError:
        Image = None
    for f in origen.iterdir():
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp") or f.name not in usadas:
            continue
        dst = destino / f.name
        if Image:
            im = ImageOps.exif_transpose(Image.open(f))
            im.thumbnail((1600, 1600))
            if f.suffix.lower() in (".jpg", ".jpeg"):
                im.convert("RGB").save(dst, quality=82, optimize=True, progressive=True)
            else:
                im.save(dst, optimize=True)
        else:
            shutil.copy2(f, dst)


# ---------- construcción ----------
SITEMAP = []


def construir():
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir()
    shutil.copytree(RAIZ / "assets", SALIDA / "assets")
    copiar_fotos()
    d = CONFIG

    trabajos, consejos, servicios = cargar("trabajos"), cargar("consejos"), cargar("servicios")
    noticias = cargar("noticias") if (RAIZ / "contenido" / "noticias").exists() else []

    # --- trabajos ---
    for t in trabajos:
        fotos = [x.strip() for x in t.get("fotos", "").split(",") if x.strip()]
        galeria = ""
        if fotos:
            galeria = '<div class="gallery">' + "".join(
                f'<img src="{ruta_foto(x)}" alt="{esc(t["titulo"])}, foto {i + 1}" loading="lazy">'
                for i, x in enumerate(fotos)) + "</div>"
        facts = '<div class="facts">' + "".join(
            f"<span>{esc(v)}</span>" for v in (t.get("municipio"), t.get("servicio"), t.get("duracion")) if v) + "</div>"
        # la fecha solo se muestra si el .md la indica (fecha del trabajo); si no, «Trabajo realizado»
        eyebrow = fecha_larga(t["_fecha"]) if t.get("fecha") else "Trabajo realizado"
        cuerpo = (cabecera(eyebrow, t["titulo"], t.get("resumen", ""),
                           [("Inicio", "/"), ("Trabajos", "/trabajos/"), (t["titulo"], None)])
                  + f'<div class="wrap"><article class="prose">{facts}{markdown(t["_cuerpo"])}{galeria}{bloque_cta()}</article></div>')
        pagina(f"/trabajos/{t['slug']}/", t.get("titulo_seo") or f"{t['titulo']} · {t.get('municipio', 'Oropesa del Mar')} | SENOIDE",
               t.get("descripcion") or t.get("resumen", t["titulo"]), cuerpo,
               imagen=d["DOMINIO"] + ruta_foto(t["portada"]) if t.get("portada") else None, og_tipo="article",
               indexar=not t["_oculto"])
    trabajos = [t for t in trabajos if not t["_oculto"]]   # los ocultos no salen en listados ni en la portada
    global PUBLICADAS
    PUBLICADAS = {f"/trabajos/{t['slug']}/" for t in trabajos}

    lista_t = ('<div class="cards" data-trabajos="">' + "".join(
        tarjeta(t, "/trabajos/", f'{t.get("municipio", "")} · {t.get("servicio", "")}'.strip(" ·")) for t in trabajos) + "</div>"
               + ("" if trabajos else
                  '<div class="empty-state" id="trabajos-vacio">Abrimos el 2 de noviembre. Aquí irán apareciendo los trabajos terminados, con fotos.</div>'))
    pagina("/trabajos/", "Trabajos realizados | SENOIDE, electricista en Oropesa del Mar",
           "Instalaciones eléctricas, mantenimiento y reparaciones hechas por SENOIDE en Oropesa del Mar y la Plana.",
           cabecera("Trabajos", "Trabajos realizados", "Instalaciones y reparaciones terminadas en la zona.",
                    [("Inicio", "/"), ("Trabajos", None)])
           + f'<section style="padding-top:32px"><div class="wrap">{lista_t}</div></section>')

    # --- consejos ---
    for c in consejos:
        rev = c.get("revisado")
        nota = f'<p class="src">Publicado el {fecha_larga(c["_fecha"])}. La normativa cambia: si tienes dudas sobre tu caso, pregúntanos.</p>'
        cuerpo = (cabecera(c.get("categoria", "Consejos"), c["titulo"], c.get("resumen", ""),
                           [("Inicio", "/"), ("Consejos", "/consejos/"), (c["titulo"], None)])
                  + f'<div class="wrap"><article class="prose">{markdown(c["_cuerpo"])}{nota}{bloque_cta()}</article></div>')
        art = {"@type": "BlogPosting", "headline": c["titulo"], "description": c.get("resumen", ""),
               "datePublished": c["_fecha"].isoformat(), "dateModified": c.get("revisado", c["_fecha"].isoformat()),
               "author": {"@type": "Person", "name": d["TITULAR"]},
               "publisher": {"@id": d["DOMINIO"] + "/#empresa"},
               "mainEntityOfPage": d["DOMINIO"] + f"/consejos/{c['slug']}/", "inLanguage": "es-ES"}
        pagina(f"/consejos/{c['slug']}/", c.get("titulo_seo") or f"{c['titulo']} | SENOIDE", c.get("descripcion") or c.get("resumen", c["titulo"]), cuerpo,
               jsonld=art, og_tipo="article", indexar=not c["_oculto"])
    consejos = [c for c in consejos if not c["_oculto"]]

    lista_c = ('<div class="cards">' + "".join(
        tarjeta(c, "/consejos/", f'{c.get("categoria", "Consejos")} · {fecha_larga(c["_fecha"])}') for c in consejos) + '</div><p class="desliza" aria-hidden="true">Desliza para ver más →</p>'
               if consejos else '<div class="empty-state">Pronto publicaremos los primeros consejos.</div>')
    pagina("/consejos/", "Consejos y normativa eléctrica | SENOIDE",
           "Boletines, puntos de recarga, ahorro y seguridad eléctrica en casa explicados de forma clara.",
           cabecera("Consejos y normativa", "Consejos para tu instalación",
                    "Lo que conviene saber sobre boletines, recarga del coche, ahorro y seguridad en casa.",
                    [("Inicio", "/"), ("Consejos", None)])
           + f'<section style="padding-top:32px"><div class="wrap">{lista_c}</div></section>')

    # --- noticias ---
    for n in noticias:
        rev = n.get("revisado")
        nota = f'<p class="src">Publicado el {fecha_larga(n["_fecha"])}. Si tienes dudas sobre cómo te afecta, pregúntanos.</p>'
        cuerpo = (cabecera(n.get("categoria", "Noticias"), n["titulo"], n.get("resumen", ""),
                           [("Inicio", "/"), ("Noticias", "/noticias/"), (n["titulo"], None)])
                  + f'<div class="wrap"><article class="prose">{markdown(n["_cuerpo"])}{nota}{bloque_cta()}</article></div>')
        art = {"@type": "NewsArticle", "headline": n["titulo"], "description": n.get("resumen", ""),
               "datePublished": n["_fecha"].isoformat(), "dateModified": n.get("revisado", n["_fecha"].isoformat()),
               "author": {"@type": "Organization", "name": "SENOIDE", "url": d["DOMINIO"] + "/"},
               "publisher": {"@id": d["DOMINIO"] + "/#empresa"},
               "mainEntityOfPage": d["DOMINIO"] + f"/noticias/{n['slug']}/", "inLanguage": "es-ES"}
        pagina(f"/noticias/{n['slug']}/", n.get("titulo_seo") or f"{n['titulo']} | SENOIDE", n.get("descripcion") or n.get("resumen", n["titulo"]), cuerpo,
               jsonld=art, og_tipo="article", indexar=not n["_oculto"])
    noticias = [n for n in noticias if not n["_oculto"]]

    lista_n = ('<div class="cards">' + "".join(
        tarjeta(n, "/noticias/", f'{n.get("categoria", "Noticias")} · {fecha_larga(n["_fecha"])}') for n in noticias) + '</div><p class="desliza" aria-hidden="true">Desliza para ver más →</p>'
               if noticias else '<div class="empty-state">Pronto publicaremos las primeras noticias.</div>')
    pagina("/noticias/", "Noticias: normativa eléctrica y suministro | SENOIDE",
           "Cambios en el reglamento de baja tensión, en los contratos de luz y en las ayudas, explicados para tu casa, tu negocio o tu comunidad.",
           cabecera("Noticias", "Noticias y cambios de normativa",
                    "Lo que cambia en el reglamento eléctrico y en el suministro, y a quién afecta.",
                    [("Inicio", "/"), ("Noticias", None)])
           + f'<section style="padding-top:32px"><div class="wrap">{lista_n}</div></section>')

    # --- servicios ---
    for s in servicios:
        cuerpo = (cabecera("Servicio", s["titulo"], s.get("resumen", ""),
                           [("Inicio", "/"), ("Servicios", "/#servicios"), (s["titulo"], None)])
                  + f'<div class="wrap"><article class="prose">{markdown(s["_cuerpo"])}{bloque_cta()}</article></div>')
        srv = {"@type": "Service", "name": s["titulo"], "description": s.get("resumen", ""),
               "provider": {"@id": d["DOMINIO"] + "/#empresa"},
               "areaServed": [{"@type": "City", "name": m} for m, _z in d["ZONA"]]}
        pagina(f"/servicios/{s['slug']}/", s.get("titulo_seo", s["titulo"] + " | SENOIDE"),
               s.get("descripcion") or s.get("resumen", ""), cuerpo, jsonld=srv)

    # --- mantenimiento (página propia; en la portada queda un resumen) ---
    planes = (PLANTILLAS / "mantenimiento.html").read_text(encoding="utf-8")
    srv_mant = {"@type": "Service", "name": "Mantenimiento eléctrico con cuota fija",
                "description": "Planes de mantenimiento eléctrico para comunidades de propietarios, locales y apartamentos turísticos.",
                "provider": {"@id": d["DOMINIO"] + "/#empresa"},
                "areaServed": [{"@type": "City", "name": m} for m, _z in d["ZONA"]]}
    pagina("/mantenimiento/", "Mantenimiento eléctrico con cuota fija | SENOIDE",
           "Planes de mantenimiento eléctrico con cuota fija para comunidades, locales y apartamentos turísticos en Oropesa del Mar: visitas, informe y prioridad.",
           cabecera("Mantenimiento", "Tu electricista de referencia, con cuota fija.",
                    "Visitas programadas, informe de cada visita y prioridad cuando surge una avería. Contrato de 12 meses que se renueva solo. Puedes darte de baja cuando quieras, sin penalización: solo se liquida lo recibido frente a lo pagado.",
                    [("Inicio", "/"), ("Mantenimiento", None)])
           + f'<section id="planes" style="padding-top:32px"><div class="wrap">{planes}</div></section>', jsonld=srv_mant)

    # --- portada ---
    def bloque(titulo, eyebrow, items, base, meta, enlace_txt, vacio):
        if not items:
            return ""
        tarjetas = "".join(tarjeta(x, base, meta(x)) for x in items[:3])
        return (f'<section style="padding-top:0"><div class="wrap"><div class="section-head"><p class="eyebrow">{eyebrow}</p>'
                f'<h2>{titulo}</h2></div><div class="cards">{tarjetas}</div>'
                f'<p class="more"><a class="btn" href="{base}">{enlace_txt}</a></p></div></section>')

    inicio = (PLANTILLAS / "inicio.html").read_text(encoding="utf-8")
    inicio = inicio.replace("{{BLOQUE_TRABAJOS}}", bloque(
        "Trabajos recientes", "Trabajos", trabajos, "/trabajos/",
        lambda t: f'{t.get("municipio", "")} · {t.get("servicio", "")}'.strip(" ·"), "Ver todos los trabajos", ""))
    # Noticias y consejos en un solo bloque: los 3 artículos más recientes de las dos secciones
    articulos = sorted([(x, "/noticias/") for x in noticias] + [(x, "/consejos/") for x in consejos],
                       key=lambda a: a[0]["_fecha"], reverse=True)[:3]
    bloque_art = ""
    if articulos:
        bloque_art = ('<section style="padding-top:0"><div class="wrap"><div class="section-head"><p class="eyebrow">Noticias y consejos</p>'
                      '<h2>Normativa y consejos para tu instalación</h2></div><div class="cards">'
                      + "".join(tarjeta(x, base, f'{x.get("categoria", "Noticias" if base == "/noticias/" else "Consejos")} · {fecha_larga(x["_fecha"])}')
                                for x, base in articulos)
                      + '</div><p class="desliza" aria-hidden="true">Desliza para ver más →</p><p class="more">'
                      + ('<a class="btn" href="/noticias/">Ver noticias</a> ' if noticias else "")
                      + ('<a class="btn" href="/consejos/">Ver consejos</a>' if consejos else "")
                      + '</p></div></section>')
    inicio = inicio.replace("{{BLOQUE_ARTICULOS}}", bloque_art)
    opiniones = ""
    if d["RESENAS_URL"] or d["PERFIL_GOOGLE"]:
        opiniones = ('<div class="ccard"><div><div class="k">Google</div>'
                     + (f'<a class="v small" href="{esc(d["PERFIL_GOOGLE"])}" target="_blank" rel="noopener">Nuestra ficha en Google</a>' if d["PERFIL_GOOGLE"] else "")
                     + (f'<a class="v small" href="{esc(d["RESENAS_URL"])}" target="_blank" rel="noopener">¿Ya has trabajado con nosotros? Déjanos tu opinión</a>' if d["RESENAS_URL"] else "")
                     + '</div></div>')
    inicio = inicio.replace("{{OPINIONES}}", opiniones)
    # zona de trabajo (portada) y municipios de la calculadora, desde la misma lista
    TRAMOS = [("Sin desplazamiento", "incluido"), ("Hasta 20 km", "+15 € por visita"), ("De 20 a 40 km", "+30 € por visita")]
    zona_html = "".join(
        f'<div class="tramo"><p class="tramo-t"><b>{t}</b> · {pr}</p><div class="towns">'
        + "".join('<span class="home">' + esc(m) + '</span>' if z == 0 else '<span>' + esc(m) + '</span>' for m, z in d["ZONA"] if z == i)
        + '</div></div>' for i, (t, pr) in enumerate(TRAMOS))
    inicio = inicio.replace("{{ZONA_TRAMOS}}", zona_html)
    muni_opts = '<option value="">Elige el municipio</option>' + "".join(
        f'<optgroup label="{t} ({pr})">' + "".join(f'<option value="{esc(m)}" data-z="{z}">{esc(m)}</option>' for m, z in d["ZONA"] if z == i) + '</optgroup>'
        for i, (t, pr) in enumerate(TRAMOS)) + '<option value="otro" data-z="">Otro municipio</option>'
    inicio = inicio.replace("{{MUNI_OPCIONES}}", muni_opts)
    inicio = (inicio.replace("{{TELEFONO}}", d["TELEFONO"])
              .replace("{{TELEFONO_SIN_ESPACIOS}}", d["TELEFONO"].replace(" ", ""))
              .replace("{{EMAIL}}", d["EMAIL"]).replace("{{WHATSAPP}}", d["WHATSAPP"]))
    faq = {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": "¿Qué es el boletín eléctrico?",
         "acceptedAnswer": {"@type": "Answer", "text": "Es el Certificado de Instalación Eléctrica (CIE). Lo firma un instalador habilitado y lo pide la distribuidora para dar de alta la luz, cambiar de titular tras años sin suministro o subir la potencia."}},
        {"@type": "Question", "name": "¿El precio de la calculadora es el definitivo?",
         "acceptedAnswer": {"@type": "Answer", "text": "No. Es un precio medio con material de gama comercial incluido. Si quieres otra gama o un modelo concreto, se presupuesta aparte. En la visita vemos tu caso y te damos el presupuesto por escrito antes de empezar. Si al abrir aparece algo que no se veía, te lo explicamos y no hacemos nada sin tu aprobación."}}]}
    pagina("/", "Electricista en Oropesa del Mar y Castellón | SENOIDE",
           "Electricista certificado en Oropesa del Mar, Benicàssim y Castellón: averías, boletines CIE, cuadros, puntos de recarga y mantenimiento. Calcula tu presupuesto.",
           inicio, jsonld=faq)

    # --- páginas legales ---
    for slug, titulo, fichero in (("aviso-legal", "Aviso legal", "aviso-legal.md"),
                                  ("privacidad", "Política de privacidad", "privacidad.md"),
                                  ("cookies", "Política de cookies", "cookies.md"),
                                  ("condiciones-mantenimiento", "Condiciones de los planes de mantenimiento", "condiciones-mantenimiento.md"),
                                  ("desistimiento", "Derecho de desistimiento", "desistimiento.md")):
        texto = (RAIZ / "contenido" / "legal" / fichero).read_text(encoding="utf-8")
        for k in ("TITULAR", "NIF", "DOMICILIO", "EMAIL", "TELEFONO", "DOMINIO"):
            texto = texto.replace("{{" + k + "}}", d[k])
        pagina(f"/{slug}/", f"{titulo} | SENOIDE", f"{titulo} de la web de SENOIDE.",
               cabecera("Información legal", titulo, migas=[("Inicio", "/"), (titulo, None)])
               + f'<div class="wrap"><article class="prose">{markdown(texto)}</article></div>', indexar=False)

    # --- baja del mantenimiento (cláusula 6.2: también se puede pedir por la web) ---
    form_baja = (
        '<div class="wrap" style="padding-block:24px 64px"><article class="prose">'
        '<p>Puedes darte de baja del plan de mantenimiento, o de uno o varios apartamentos de tu cartera, cuando quieras y sin indicar el motivo. '
        'No tiene penalización: solo se liquida lo que hayas recibido frente a lo que hayas pagado (<a href="/condiciones-mantenimiento/">condiciones</a>). Al enviar el formulario recibirás un justificante con la fecha y la hora de recepción, y después la confirmación por escrito de la fecha de efecto y, si corresponde, de lo que te devolvemos o de lo que quede pendiente.</p>'
        '<form class="form" id="baja-form" novalidate>'
        '<div class="field"><label for="b-nombre">Titular del contrato</label><input id="b-nombre" autocomplete="name" placeholder="Nombre y apellidos o razón social"></div>'
        '<div class="field"><label for="b-email">Correo</label><input id="b-email" type="email" autocomplete="email" placeholder="Para enviarte el justificante"></div>'
        '<div class="field"><label for="b-tel">Teléfono (opcional)</label><input id="b-tel" type="tel" autocomplete="tel"></div>'
        '<div class="field"><label for="b-contrato">N.º de contrato (si lo tienes)</label><input id="b-contrato" placeholder="CT-2026-0001"></div>'
        '<div class="field"><span style="font-weight:600">¿De qué te das de baja?</span>'
        '<label style="display:flex;gap:10px;align-items:center;font-weight:400;margin:8px 0 0"><input type="radio" name="b-alc" id="b-alc-todo" checked style="width:auto;margin:0"> De todo el contrato</label>'
        '<label style="display:flex;gap:10px;align-items:center;font-weight:400;margin:8px 0 0"><input type="radio" name="b-alc" id="b-alc-aptos" style="width:auto;margin:0"> De algunos apartamentos de mi cartera</label></div>'
        '<div class="field" id="b-aptos-w" hidden><label for="b-aptos">Apartamentos que das de baja</label><textarea id="b-aptos" rows="2" placeholder="Nombre o dirección de cada apartamento"></textarea></div>'
        '<div class="field"><span style="font-weight:600">¿Desde cuándo?</span>'
        '<label style="display:flex;gap:10px;align-items:center;font-weight:400;margin:8px 0 0"><input type="radio" name="b-modo" id="b-modo-recepcion" value="recepcion" checked style="width:auto;margin:0"> Desde que recibamos esta solicitud (hoy)</label>'
        '<label style="display:flex;gap:10px;align-items:center;font-weight:400;margin:8px 0 0"><input type="radio" name="b-modo" id="b-modo-finmes" value="finmes" style="width:auto;margin:0"> Al final de este mes</label>'
        '<label style="display:flex;gap:10px;align-items:center;font-weight:400;margin:8px 0 0"><input type="radio" name="b-modo" id="b-modo-fecha" value="fecha" style="width:auto;margin:0"> En una fecha posterior que elijo</label></div>'
        '<div class="field" id="b-fecha-w" hidden><label for="b-fecha">Fecha de efecto</label><input id="b-fecha" type="date"><small>No puede ser anterior a hoy.</small></div>'
        '<div class="field"><label for="b-com">Comentario (opcional)</label><textarea id="b-com" rows="3"></textarea></div>'
        '<input id="b-web" type="text" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">'
        '<label class="priv"><input type="checkbox" id="b-priv"><span>He leído la <a href="/privacidad/" target="_blank">política de privacidad</a> y he sido informado del tratamiento de mis datos para gestionar la baja.</span></label>'
        '<p><button class="btn primary" id="b-send" type="submit">Enviar la solicitud de baja</button></p>'
        '<div id="b-msg" role="status"></div></form>'
        f'<p class="small">También puedes pedir la baja por correo a {d["EMAIL"]}, por WhatsApp al {d["TELEFONO"]}, por escrito o en persona. '
        '<a href="/condiciones-mantenimiento/">Condiciones de los planes</a>.</p>'
        '</article></div><script src="/assets/baja.js?v=' + VERSION + '" defer></script>')
    pagina("/baja/", "Darse de baja del mantenimiento | SENOIDE", "Formulario para darse de baja de un plan de mantenimiento de SENOIDE, sin penalización.",
           cabecera("Mantenimiento", "Darte de baja", "Sin permanencia ni penalización.", [("Inicio", "/"), ("Mantenimiento", "/mantenimiento/"), ("Baja", None)])
           + form_baja, indexar=False)

    # --- 404, sitemap, robots ---
    pagina("/404-tmp/", "Página no encontrada | SENOIDE", "La página que buscas no existe.",
           cabecera("Error 404", "Esta página no existe", "Puede que el enlace esté mal o que la hayamos movido.")
           + '<div class="wrap" style="padding-block:32px 72px"><a class="btn primary" href="/">Volver al inicio</a></div>',
           indexar=False)
    (SALIDA / "404-tmp" / "index.html").rename(SALIDA / "404.html")
    (SALIDA / "404-tmp").rmdir()

    hoy = os.environ.get("WEB_FECHA") or dt.date.today().isoformat()
    (SALIDA / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{hoy}</lastmod></url>\n" for u in SITEMAP) + "</urlset>\n",
        encoding="utf-8")
    (SALIDA / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {d['DOMINIO']}/sitemap.xml\n", encoding="utf-8")
    print(f"Listo: {len(SITEMAP)} páginas en {SALIDA}")
    print(f"  trabajos: {len(trabajos)} · consejos: {len(consejos)} · noticias: {len(noticias)} · servicios: {len(servicios)}")
    for k in ("NIF", "DOMICILIO"):
        if "pendiente" in d[k]:
            print(f"  AVISO: falta completar {k} en CONFIG (obligatorio en el aviso legal).")


if __name__ == "__main__":
    construir()
    if "--ver" in sys.argv:
        import functools, http.server
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SALIDA))
        print("Abre http://localhost:8000  (Ctrl+C para parar)")
        http.server.ThreadingHTTPServer(("localhost", 8000), h).serve_forever()
