import os
import json
from typing import List, Dict, Any
from logger import logger

BASE_URL = "https://radardeprecos.github.io/radar/"

def build_homepage(input_path: str, template_path: str, output_path: str) -> None:
    logger.info(f"Construindo página inicial a partir de {input_path}...")
    
    products = []
    if os.path.exists(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {input_path}: {e}")

    # Atualizar JSON para JS
    json_output_path = "data/products/offers.json"
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    if not os.path.exists(template_path):
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    def _safe_url(p):
        aff = p.get('custom_affiliate_url', '')
        if aff and '/social/' not in aff and 'vendas0nline?' not in aff:
            return aff
        return p.get('permalink', '')

    # Renderizar hero section
    hero_product = products[0] if products else None
    featured_products = products[1:13] if len(products) > 1 else []
    
    hero_html = "" 
    if hero_product:
        hero_html = f"""
        <div class="hero-card">
            <div class="hero-img"><img src="{hero_product.get("image", hero_product.get("thumbnail", ""))}" alt="{hero_product.get("name", "")}"></div>
            <div class="hero-info">
                <span class="badge">↓ {hero_product.get("custom_discount_pct", 0)}%</span>
                <h1>{hero_product.get("name", "")}</h1>
                <div class="price-tag">R$ {hero_product.get("price", 0):.2f} <span class="old-price">R$ {hero_product.get("originalPrice", 0):.2f}</span></div>
                <a href="{_safe_url(hero_product)}" class="btn" target="_blank">🛒 Ver oferta no Mercado Livre</a>
            </div>
        </div>
        """
        
    featured_grid_html = ""
    if featured_products:
        for p in featured_products:
            featured_grid_html += f"""
            <div class="product-card">
                <span class="badge">↓ {p.get("custom_discount_pct", 0)}%</span>
                <div class="card-img"><img src="{p.get("image", p.get("thumbnail", ""))}" alt="{p.get("name", "")}"></div>
                <h3>{p.get("name", "")[:50]}...</h3>
                <div class="price-tag" style="font-size: 20px;">R$ {p.get("price", 0):.2f}</div>
                <a href="{_safe_url(p)}" class="btn" style="width: 100%; text-align: center;" target="_blank">Ver</a>
            </div>
            """
    else:
        featured_grid_html = "<p style='grid-column: 1/-1; text-align: center;'>Nenhuma oferta disponível no momento.</p>"
        
    # SEO DINÂMICO (Fase 1)
    seo_title = "Radar de Preços — As Melhores Ofertas do Mercado Livre Hoje"
    meta_desc = "Economize com as melhores ofertas curadas do Mercado Livre. Monitoramos preços em tempo real para você encontrar o maior desconto."
    canonical_url = BASE_URL

    # Substituições no template
    page_content = template.replace("{{seo.title}}", seo_title)
    page_content = page_content.replace("{{meta.description}}", meta_desc)
    page_content = page_content.replace("{{canonical.url}}", canonical_url)
    page_content = page_content.replace("{{hero_section}}", hero_html)
    page_content = page_content.replace("{{featured_products_grid}}", featured_grid_html)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(page_content)

if __name__ == "__main__":
    build_homepage("data/new_offers.json", "templates/homepage.html", "index.html")
