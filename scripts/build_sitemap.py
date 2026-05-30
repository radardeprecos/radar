import os
import json
from datetime import datetime
from typing import List, Dict, Any
from logger import logger

BASE_URL = "https://radardeprecos.github.io/radar/"

def slugify(text: str) -> str:
    text = text.lower()
    text = text.replace(" ", "-")
    # BUGFIX: Corrigido "." para ""
    text = "".join(c for c in text if c.isalnum() or c == "-")
    return text

def generate_sitemap(products_path: str, output_path: str) -> None:
    logger.info("Gerando sitemap.xml...")
    
    urls = []
    # Adicionar páginas estáticas
    static_pages = [
        "", # Homepage
        "sobre/",
        "contato/",
        "privacidade/",
        "termos/",
        "quem-somos/",
    ]
    for page in static_pages:
        urls.append({"loc": f"{BASE_URL}{page}", "lastmod": datetime.now().isoformat()})
        
    # Adicionar páginas de produtos e categorias
    products = []
    if os.path.exists(products_path):
        try:
            with open(products_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {products_path} para sitemap: {e}")

    categories = set()
    for product in products:
        # Produtos
        product_name = product.get("name") or product.get("title") or ""
        product_id = product.get("id", "")
        product_slug = slugify(product_name)
        category_slug = product.get("custom_category_slug", "")
        
        if product_slug and product_id and category_slug:
            product_url = f"{BASE_URL}ofertas/{category_slug}/{product_slug}-{product_id}.html"
            urls.append({"loc": product_url, "lastmod": datetime.now().isoformat()})
        
        # Coletar categorias
        if category_slug:
            categories.add(category_slug)
            
    # Adicionar categorias ao sitemap
    for category_slug in categories:
        category_url = f"{BASE_URL}categorias/{category_slug}/"
        urls.append({"loc": category_url, "lastmod": datetime.now().isoformat()})

    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url_data in urls:
        sitemap_content += "    <url>\n"
        sitemap_content += f"        <loc>{url_data['loc']}</loc>\n"
        sitemap_content += f"        <lastmod>{url_data['lastmod']}</lastmod>\n"
        sitemap_content += "        <changefreq>hourly</changefreq>\n"
        sitemap_content += "        <priority>0.8</priority>\n"
        sitemap_content += "    </url>\n"
    
    sitemap_content += "</urlset>"
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sitemap_content)
        logger.info(f"Sitemap gerado com {len(urls)} URLs em {output_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar sitemap: {e}")

if __name__ == "__main__":
    try:
        generate_sitemap("data/new_offers.json", "sitemap.xml")
    except Exception as e:
        logger.error(f"Erro fatal ao gerar sitemap: {e}")
