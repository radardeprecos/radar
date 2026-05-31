import os
import json
from datetime import datetime
from typing import List, Dict, Any
from logger import logger

BASE_URL = "https://radardeprecos.github.io/radar/"

def slugify(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().replace(' ', '-')
    return ''.join(c for c in text if c.isalnum() or c == '-')

def generate_sitemap(db_path: str, output_path: str) -> None:
    logger.info("Gerando sitemap.xml permanente...")
    
    urls = []
    # Adicionar páginas estáticas
    static_pages = [
        "", "noticias/", "comparar/", "melhores-2026/", "estatisticas/", 
        "black-friday/", "meus-favoritos/", "glossario/", "marcas/",
        "alertas/", "sobre/", "contato/", "privacidade/", "termos/", "quem-somos/"
    ]
    for page in static_pages:
        urls.append({"loc": f"{BASE_URL}{page}", "lastmod": datetime.now().isoformat(), "priority": "1.0"})
        
    # Carregar banco de dados COMPLETO
    all_products = []
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                all_products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar banco para sitemap: {e}")

    categories = set()
    for p in all_products:
        p_name = p.get("name") or p.get("title") or ""
        p_id = p.get("id", "")
        p_slug = slugify(p_name)
        p_cat_slug = p.get("custom_category_slug", "outros")
        p_status = p.get("status", "active")
        
        if p_slug and p_id and p_cat_slug:
            p_url = f"{BASE_URL}ofertas/{p_cat_slug}/{p_slug}-{p_id}.html"
            # Prioridade maior para produtos ativos
            priority = "0.8" if p_status == "active" else "0.5"
            urls.append({"loc": p_url, "lastmod": datetime.now().isoformat(), "priority": priority})
            categories.add(p_cat_slug)
            
    # Adicionar categorias
    for cat in categories:
        urls.append({"loc": f"{BASE_URL}categorias/{cat}/", "lastmod": datetime.now().isoformat(), "priority": "0.7"})

    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for u in urls:
        sitemap_content += f"""    <url>
        <loc>{u['loc']}</loc>
        <lastmod>{u['lastmod']}</lastmod>
        <changefreq>hourly</changefreq>
        <priority>{u['priority']}</priority>
    </url>\n"""
    
    sitemap_content += "</urlset>"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    logger.info(f"Sitemap permanente gerado com {len(urls)} URLs.")

if __name__ == "__main__":
    generate_sitemap("data/database/all_products.json", "sitemap.xml")
