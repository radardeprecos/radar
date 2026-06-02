import os
import json
import unicodedata
from pathlib import Path
from logger import logger

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().replace(' ', '-')
    return ''.join(c for c in text if c.isalnum() or c == '-')

def money(value):
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "N/A"

def build_homepage(input_path, template_path, output_path):
    logger.info(f"Construindo página inicial estática...")
    
    if not os.path.exists(template_path):
        logger.error(f"Template {template_path} não encontrado!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    products = []
    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            products = json.load(f)
    
    active_products = [p for p in products if p.get("status") == "active"]
    # Top 24 produtos com maior desconto
    active_products.sort(key=lambda x: x.get("custom_discount_pct", 0), reverse=True)
    display_products = active_products[:24]

    products_html = ""
    for p in display_products:
        p_name = p.get("name") or p.get("title") or "Produto"
        p_id = p.get("id", "")
        p_slug = slugify(p_name)
        p_cat = p.get("custom_category_slug", "outros")
        p_url = f"ofertas/{p_cat}/{p_slug}-{p_id}.html"
        p_img = p.get("image") or p.get("thumbnail") or ""
        p_price = money(p.get("price"))
        p_old = money(p.get("originalPrice") or p.get("original_price"))
        p_disc = p.get("custom_discount_pct", 0)

        products_html += f"""
        <div class="product-card">
            <div class="badge-discount">{p_disc}% OFF</div>
            <img src="{p_img}" alt="{p_name}" class="product-image">
            <h3 class="product-title">{p_name}</h3>
            <div class="price-container">
                <span class="price-current">{p_price}</span>
                <span class="price-old">{p_old}</span>
            </div>
            <a href="{p_url}" class="btn">VER ALERTA</a>
        </div>
        """

    content = template.replace("{{products_html}}", products_html)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Homepage gerada com {len(display_products)} produtos.")

if __name__ == "__main__":
    build_homepage("data/database/all_products.json", "templates/homepage.html", "index.html")
