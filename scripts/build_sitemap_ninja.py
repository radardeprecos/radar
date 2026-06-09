#!/usr/bin/env python3
"""
Gerador de Sitemap Ninja
Gera sitemap.xml completo com todas as páginas do site.
"""

import os
from datetime import datetime
from pathlib import Path

BASE_URL = "https://radardeprecos.github.io/radar"
ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now().strftime("%Y-%m-%d")


def get_all_pages():
    """Coleta todas as páginas HTML do site."""
    pages = []

    # Páginas estáticas principais
    static_pages = [
        ("", 1.0, "daily"),
        ("categorias/", 0.9, "daily"),
        ("comparativos/", 0.9, "weekly"),
        ("noticias/", 0.8, "daily"),
        ("sobre/", 0.5, "monthly"),
        ("privacidade/", 0.3, "monthly"),
        ("termos/", 0.3, "monthly"),
        ("contato/", 0.4, "monthly"),
    ]
    for path, priority, freq in static_pages:
        pages.append((f"{BASE_URL}/{path}", priority, freq))

    # Páginas de categorias
    cat_dirs = [d for d in (ROOT / "categorias").iterdir() if d.is_dir()] if (ROOT / "categorias").exists() else []
    for cat_dir in cat_dirs:
        pages.append((f"{BASE_URL}/categorias/{cat_dir.name}/", 0.8, "daily"))

    # Páginas de produto
    for html_file in sorted((ROOT / "ofertas").rglob("*.html")):
        rel = html_file.relative_to(ROOT)
        pages.append((f"{BASE_URL}/{rel}", 0.7, "daily"))

    # Comparativos (nova pasta)
    for html_file in sorted((ROOT / "comparativos").glob("*.html")):
        if html_file.name != "index.html":
            pages.append((f"{BASE_URL}/comparativos/{html_file.name}", 0.8, "weekly"))

    # Comparativos antigos (pasta comparar)
    if (ROOT / "comparar").exists():
        for html_file in sorted((ROOT / "comparar").glob("*.html")):
            pages.append((f"{BASE_URL}/comparar/{html_file.name}", 0.7, "weekly"))

    # Blog/notícias
    if (ROOT / "noticias").exists():
        for html_file in sorted((ROOT / "noticias").glob("*.html")):
            if html_file.name != "index.html":
                pages.append((f"{BASE_URL}/noticias/{html_file.name}", 0.6, "weekly"))

    return pages


def generate_sitemap(pages):
    """Gera o XML do sitemap."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"')
    lines.append('        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">')

    for url, priority, freq in pages:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{NOW}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{priority:.1f}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>")
    return "\n".join(lines)


def main():
    print("🗺️  Gerando sitemap...")
    pages = get_all_pages()
    print(f"   {len(pages)} URLs encontradas")

    sitemap_xml = generate_sitemap(pages)
    sitemap_path = ROOT / "sitemap.xml"
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    print(f"   ✅ sitemap.xml salvo ({len(pages)} URLs)")

    # Gerar robots.txt atualizado
    robots = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml

# Bloquear páginas desnecessárias
Disallow: /assets/
Disallow: /scripts/
Disallow: /data/
"""
    robots_path = ROOT / "robots.txt"
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(robots)
    print("   ✅ robots.txt atualizado")


if __name__ == "__main__":
    main()
