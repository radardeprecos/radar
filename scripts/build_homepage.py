import os
import json
from typing import List, Dict, Any
from logger import logger

def build_homepage(input_path: str, template_path: str, output_path: str) -> None:
    logger.info(f"Construindo página inicial a partir de {input_path}...")
    if not os.path.exists(input_path):
        logger.error(f"Arquivo de entrada {input_path} não encontrado!")
        return
        
    with open(input_path, "r", encoding="utf-8") as f:
        products = json.load(f)
        
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    # Preparar dados para o template
    hero_product = products[0] if products else None
    featured_products = products[1:13] # 12 produtos para a grade
    
    # Renderizar hero section
    hero_html = "" 
    if hero_product:
        hero_html = f"""
        <div class="hero-card">
            <div class="hero-img"><img src="{hero_product.get("custom_image_url", "")}" alt="{hero_product.get("name", "")}"></div>
            <div class="hero-info">
                <span class="badge">↓ {hero_product.get("custom_discount_pct", 0)}%</span>
                <h1>{hero_product.get("name", "")}</h1>
                <div class="price-tag">R$ {hero_product.get("price", 0):.2f} <span class="old-price">R$ {hero_product.get("originalPrice", 0):.2f}</span></div>
                <a href="{hero_product.get("custom_affiliate_url", "")}" class="btn" target="_blank">🛒 Ver oferta no Mercado Livre</a>
            </div>
        </div>
        """
        
    # Renderizar featured products grid
    featured_grid_html = ""
    for p in featured_products:
        featured_grid_html += f"""
        <div class="product-card">
            <span class="badge">↓ {p.get("custom_discount_pct", 0)}%</span>
            <div class="card-img"><img src="{p.get("custom_image_url", "")}" alt="{p.get("name", "")}"></div>
            <h3>{p.get("name", "")[:50]}...</h3>
            <div class="price-tag" style="font-size: 20px;">R$ {p.get("price", 0):.2f}</div>
            <a href="{p.get("custom_affiliate_url", "")}" class="btn" style="width: 100%; text-align: center;" target="_blank">Ver</a>
        </div>
        """
        
    # Substituições no template principal
    page_content = template.replace("{{hero_section}}", hero_html)
    page_content = page_content.replace("{{featured_products_grid}}", featured_grid_html)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page_content)
        
    logger.info(f"Página inicial gerada: {output_path}")

if __name__ == "__main__":
    build_homepage("data/new_offers.json", "templates/homepage.html", "index.html")
