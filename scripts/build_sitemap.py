import os
import json
from datetime import datetime
from typing import List, Dict, Any
from logger import logger

BASE_URL = "https://radardeprecos.github.io/radar/"

def slugify(text: str) -> str:
    text = text.lower()
    text = text.replace(" ", "-")
    text = ".".join(c for c in text if c.isalnum() or c == "-")
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
        
    # Adicionar páginas de produtos
    if os.path.exists(products_path):
        with open(products_path, "r", encoding="utf-8") as f:
            products = json.load(f)
            for product in products:
                product_name = product.get("name", "")
                product_id = product.get("id", "")
                product_slug = slugify(product_name)
                category_slug = product.get("custom_category_slug", "")
                
                if product_slug and product_id and category_slug:
                    product_url = f"{BASE_URL}ofertas/{category_slug}/{product_slug}-{product_id}.html"
                    urls.append({"loc": product_url, "lastmod": datetime.now().isoformat()})
                    
    # Adicionar páginas de categorias
    categories = set()
    if os.path.exists(products_path):
        with open(products_path, "r", encoding="utf-8") as f:
            products = json.load(f)
            for product in products:
                category_slug = product.get("custom_category_slug", "")
                if category_slug:
                    categories.add(category_slug)
                    
    for category_slug in categories:
        category_url = f"{BASE_URL}categorias/{category_slug}/"
        urls.append({"loc": category_url, "lastmod": datetime.now().isoformat()})

    sitemap_content = """
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for url_data in urls:
        sitemap_content += f"""
    <url>
        <loc>{url_data["loc"]}</loc>
        <lastmod>{url_data["lastmod"]}</lastmod>
        <changefreq>hourly</changefreq>
        <priority>0.8</priority>
    </url>
"""
    sitemap_content += "</urlset>"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
        
    logger.info(f"Sitemap gerado com {len(urls)} URLs em {output_path}")

if __name__ == "__main__":
    generate_sitemap("data/new_offers.json", "sitemap.xml")
