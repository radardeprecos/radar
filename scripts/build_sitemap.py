import os
import json
from datetime import datetime
from logger import logger

def generate_sitemap():
    logger.info("Gerando sitemap.xml como sitemapindex...")
    base_url = "https://radardeprecos.github.io/radar"
    
    # 1. Primeiro gerar o sitemap-legado.xml (o que era o sitemap.xml antes)
    urls = [
        {"loc": f"{base_url}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{base_url}/noticias/", "priority": "0.8", "changefreq": "daily"},
        {"loc": f"{base_url}/melhores-ofertas/", "priority": "0.9", "changefreq": "hourly"},
    ]
    seen_locs = {u["loc"] for u in urls}
    
    db_path = "data/database/all_products.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            products = json.load(f)
            for p in products:
                slug = p.get('slug') or p.get('id')
                category = p.get('category', 'geral').lower().replace(' ', '-')
                loc = f"{base_url}/ofertas/{category}/{slug}.html"
                if loc not in seen_locs:
                    urls.append({"loc": loc, "priority": "0.6", "changefreq": "weekly"})
                    seen_locs.add(loc)
    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    xml_content = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_content.append(f'    <url>')
        xml_content.append(f'        <loc>{u["loc"]}</loc>')
        xml_content.append(f'        <lastmod>{now}</lastmod>')
        xml_content.append(f'        <changefreq>{u["changefreq"]}</changefreq>')
        xml_content.append(f'        <priority>{u["priority"]}</priority>')
        xml_content.append(f'    </url>')
    xml_content.append('</urlset>')
    
    with open("sitemap-legado.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_content))
    
    # 2. Agora gerar o sitemap.xml como sitemapindex (Master)
    sitemaps = [
        "sitemap-paginas.xml",
        "sitemap-noticias.xml",
        "sitemap-produtos.xml",
        "sitemap-categorias.xml",
        "sitemap-guias.xml",
        "sitemap-comparativos.xml",
        "sitemap-rankings.xml",
        "sitemap-legado.xml"
    ]
    
    index_lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                   '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for s in sitemaps:
        index_lines.append("  <sitemap>")
        index_lines.append(f"    <loc>{base_url}/{s}</loc>")
        index_lines.append(f"    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>")
        index_lines.append("  </sitemap>")
    index_lines.append("</sitemapindex>")
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")
        
    logger.info("Sitemap Index (sitemap.xml) restaurado com sucesso.")

if __name__ == "__main__":
    generate_sitemap()
