#!/usr/bin/env python3
"""
Generador de Brújula Patrimonial — AMG Strategic Investments
--------------------------------------------------------------
Toma el archivo de contenido de la nueva edición (content/edicionNN.md)
y actualiza AMG_Brujula_Patrimonial.html:

  1. Mueve la edición que hoy está en "Lectura de la semana" al archivo
     (<details class="archive-item">), usando la fecha que quedó guardada
     como metadato invisible cuando esa edición se publicó.
  2. Inserta la nueva edición como la "Lectura de la semana" vigente.

No requiere librerías externas — solo Python estándar.

Uso:
    python3 build/generar_html.py content/edicion-04.md
"""
import re
import sys
import html
from pathlib import Path

HTML_PATH = Path("AMG_Brujula_Patrimonial.html")
ARCHIVE_MARKER = '<div class="section-label">Ediciones anteriores</div>'


def parse_content_file(path: str):
    """Lee el archivo de contenido: bloque de metadatos --- --- + párrafos separados por línea en blanco."""
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(
            "El archivo debe empezar con un bloque de metadatos entre '---' y '---' "
            "(numero, titulo, fecha_semana). Revisa la plantilla de ejemplo."
        )
    meta_block, body = m.groups()

    meta = {}
    for line in meta_block.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')

    for campo in ("numero", "titulo", "fecha_semana"):
        if campo not in meta:
            raise ValueError(f"Falta el campo obligatorio '{campo}' en los metadatos del archivo.")

    paragraphs = [p.strip() for p in body.strip().split("\n\n") if p.strip()]
    if not paragraphs:
        raise ValueError("El archivo no tiene párrafos de contenido.")

    return meta, paragraphs


def esc(text: str) -> str:
    """Escapa & < > sin tocar comillas ni tildes/ñ (para no romper el HTML)."""
    return html.escape(text, quote=False)


def build_article_html(meta: dict, paragraphs: list[str]) -> str:
    parrafos_html = "\n".join(f"<p>{esc(p)}</p>" for p in paragraphs)
    return (
        f'<article class="reading">\n'
        f'<div class="reading-meta" data-fecha-semana="{esc(meta["fecha_semana"])}">'
        f'Edición {meta["numero"]} · Brújula Patrimonial</div>\n'
        f'<div class="reading-title-row">\n'
        f'<h3>{esc(meta["titulo"])}</h3>\n'
        f'</div>\n'
        f'{parrafos_html}\n'
        f'<div class="signature">\n'
        f'<div class="name">Aldo Mallma</div>\n'
        f'<div class="role">Fundador, AMG Strategic Investments · amgpatrimonial.com</div>\n'
        f'</div>\n'
        f'<div class="disclaimer-note">Esto es una lectura de mercado y de método, no una '
        f'recomendación de inversión personalizada — cada arquitectura patrimonial se diseña '
        f'según el perfil de cada persona.</div>\n'
        f'</article>'
    )


def build_archive_item(numero: str, titulo: str, fecha_semana: str, body_html: str) -> str:
    return (
        f'<details class="archive-item">\n'
        f'<summary>\n'
        f'<span>Edición {numero} — {titulo}</span>\n'
        f'<span class="archive-date">Semana del {fecha_semana} <span class="arrow">›</span></span>\n'
        f'</summary>\n'
        f'<div class="archive-body">\n'
        f'{body_html}\n'
        f'</div>\n'
        f'</details>'
    )


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 build/generar_html.py content/edicionNN.md")
        sys.exit(1)

    meta, paragraphs = parse_content_file(sys.argv[1])
    html_text = HTML_PATH.read_text(encoding="utf-8")

    # 1. Extraer el <article class="reading">...</article> vigente (edición saliente)
    article_match = re.search(r'<article class="reading">.*?</article>', html_text, re.DOTALL)
    if not article_match:
        raise ValueError("No se encontró <article class='reading'> en el HTML actual.")
    old_article = article_match.group(0)

    # 2. Datos de la edición saliente (número, título, fecha guardada como metadato)
    meta_match = re.search(
        r'<div class="reading-meta" data-fecha-semana="([^"]*)">Edición (\d+) · Brújula Patrimonial</div>',
        old_article,
    )
    title_match = re.search(r'<h3>(.*?)</h3>', old_article, re.DOTALL)

    if not meta_match:
        print(
            "⚠️  La edición actual no tiene el atributo data-fecha-semana guardado "
            "(probablemente porque se publicó antes de instalar este sistema).\n"
            "    Necesito que me digas la fecha de esa semana para poder archivarla correctamente."
        )
        sys.exit(1)

    old_fecha, old_num = meta_match.group(1), meta_match.group(2)
    old_titulo = title_match.group(1).strip() if title_match else "(título no encontrado)"

    # 3. Cuerpo de la edición saliente: todo lo que va después del título hasta cerrar </article>
    body_match = re.search(r'</div>\s*(<p>.*?)</article>', old_article, re.DOTALL)
    old_body_html = body_match.group(1).strip() if body_match else ""

    new_archive_item = build_archive_item(old_num, old_titulo, old_fecha, old_body_html)

    # 4. Insertar el archive item nuevo justo después del rótulo "Ediciones anteriores"
    if ARCHIVE_MARKER not in html_text:
        raise ValueError("No se encontró el marcador de la sección de archivo en el HTML.")
    html_text = html_text.replace(ARCHIVE_MARKER, ARCHIVE_MARKER + "\n" + new_archive_item, 1)

    # 5. Reemplazar el artículo vigente por la nueva edición
    new_article = build_article_html(meta, paragraphs)
    html_text = html_text.replace(old_article, new_article, 1)

    HTML_PATH.write_text(html_text, encoding="utf-8")
    print(f"✅ Edición {old_num} movida al archivo. Edición {meta['numero']} publicada como vigente.")


if __name__ == "__main__":
    main()
