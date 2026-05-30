import os
import json
from typing import List, Dict, Any
from logger import logger

def build_homepage(input_path: str, template_path: str, output_path: str) -> None:
    logger.info(f"Construindo página inicial a partir de {input_path}...")
    
    products = []
    if os.path.exists(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {input_path}: {e}")
    else:
        logger.warning(f"Arquivo {input_path} não encontrado. Gerando homepage com placeholders.")

    if not os.path.exists(template_path):
        logger.error(f"Template {template_path} não encontrado!")
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    # Preparar dados para o template
    hero_product = products[0] if products else None
    featured_products = products[1:13] if len(products) > 1 else []
    
    # Renderizar hero section
    hero_html = "" 
    if hero_product:
        hero_html = f"""
        <div class="hero-card">
            <div class="hero-img"><img src="{hero_product.get("image", hero_product.get("thumbnail", ""))}" alt="{hero_product.get("name", "")}"></div>
            <div class="hero-info">
                <span class="badge">↓ {hero_product.get("custom_discount_pct", 0)}%</span>
                <h1>{hero_product.get("name", "")}</h1>
                <div class="price-tag">R$ {hero_product.get("price", 0):.2f} <span class="old-price">R$ {hero_product.get("originalPrice", 0):.2f}</span></div>
                <a href="{hero_product.get("custom_affiliate_url", "")}" class="btn" target="_blank">🛒 Ver oferta no Mercado Livre</a>
            </div>
        </div>
        """
    else:
        hero_html = """
        <div class="hero-card">
            <div class="hero-info" style="width: 100%; text-align: center;">
                <h1>Radar de Preços</h1>
                <p>Estamos buscando as melhores ofertas para você. Volte em instantes!</p>
            </div>
        </div>
        """
        
    # Renderizar featured products grid
    featured_grid_html = ""
    if featured_products:
        for p in featured_products:
            featured_grid_html += f"""
            <div class="product-card">
                <span class="badge">↓ {p.get("custom_discount_pct", 0)}%</span>
                <div class="card-img"><img src="{p.get("image", p.get("thumbnail", ""))}" alt="{p.get("name", "")}"></div>
                <h3>{p.get("name", "")[:50]}...</h3>
                <div class="price-tag" style="font-size: 20px;">R$ {p.get("price", 0):.2f}</div>
                <a href="{p.get("custom_affiliate_url", "")}" class="btn" style="width: 100%; text-align: center;" target="_blank">Ver</a>
            </div>
            """
    else:
        featured_grid_html = "<p style='grid-column: 1/-1; text-align: center;'>Nenhuma oferta disponível no momento.</p>"
        
    # Substituições no template principal
    page_content = template.replace("{{hero_section}}", hero_html)
    page_content = page_content.replace("{{featured_products_grid}}", featured_grid_html)
    
    # Hardening: Se output_path não tiver diretório, garante que não quebre
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page_content)
        
    logger.info(f"Página inicial gerada: {output_path}")

if __name__ == "__main__":
    try:
        build_homepage("data/new_offers.json", "templates/homepage.html", "index.html")
    except Exception as e:
        logger.error(f"Erro fatal ao construir homepage: {e}")
