import os
import json
from typing import List, Dict, Any
from logger import logger

def slugify(text: str) -> str:
    text = text.lower().replace(" ", "-")
    return "".join(c for c in text if c.isalnum() or c == "-")

def generate_product_page(product: Dict[str, Any], template_path: str, output_dir: str) -> None:
    # CORREÇÃO DEFINITIVA: Sem aspas aninhadas na f-string
    product_name = product.get("name") or product.get("title") or "Produto"
    logger.info(f"Gerando pagina para: {product_name}")
    
    if not os.path.exists(template_path): return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    p_id = product.get("id", "0")
    p_slug = slugify(product_name)
    p_price = f"R$ {float(product.get('price', 0)):.2f}".replace(".", ",")
    p_orig = f"R$ {float(product.get('originalPrice', 0)):.2f}".replace(".", ",")
    p_img = product.get("image") or product.get("thumbnail") or ""
    p_url = product.get("custom_affiliate_url") or product.get("permalink") or ""
    p_cat = product.get("custom_category_slug", "geral")
    
    content = template.replace("{{product.name}}", product_name)
    content = content.replace("{{product.price}}", p_price)
    content = content.replace("{{product.originalPrice}}", p_orig)
    content = content.replace("{{product.image}}", p_img)
    content = content.replace("{{product.url}}", p_url)
    content = content.replace("{{product.category}}", p_cat.title())
    
    path = os.path.join(output_dir, p_cat, f"{p_slug}-{p_id}.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def generate_all(input_p: str, temp_p: str, out_d: str) -> None:
    if not os.path.exists(input_p): return
    with open(input_p, "r", encoding="utf-8") as f:
        products = json.load(f)
    for p in products:
        generate_product_page(p, temp_p, out_d)

if __name__ == "__main__":
    generate_all("data/new_offers.json", "templates/product_template.html", "ofertas")
