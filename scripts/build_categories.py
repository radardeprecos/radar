import os
import json
from typing import List, Dict, Any
from logger import logger

BASE_URL = "https://radardeprecos.github.io/radar/"

def build_category_page(category_slug: str, products: List[Dict[str, Any]], template_path: str, output_dir: str) -> None:
    logger.info(f"Gerando página PREMIUM para a categoria: {category_slug}")
    
    if not os.path.exists(template_path):
        logger.error(f"Template {template_path} não encontrado!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    category_name = category_slug.replace("-", " ").title()
    
    def _safe_url(p):
        aff = p.get('custom_affiliate_url', '')
        if aff and 'http' in aff:
            return aff
        return p.get('permalink', '')

    # Renderizar produtos da categoria com novo design de cards
    category_products_html = ""
    for p in products:
        img_url = p.get("image") or p.get("thumbnail")
        product_url = _safe_url(p)
        
        # Pular se não tiver imagem ou link (Garantia de qualidade)
        if not img_url or not product_url or len(img_url) < 10:
            continue

        discount = p.get("custom_discount_pct", 0)
        p_name = p.get("name") or p.get("title") or "Produto"
        price = p.get("price", 0)
        old_price = p.get("originalPrice") or p.get("original_price") or price

        category_products_html += f"""
        <div class="product-card">
            <span class="badge-discount">↓ {discount}% OFF</span>
            <div class="img-wrapper">
                <img src="{img_url}" alt="{p_name}" loading="lazy">
            </div>
            <div class="card-body">
                <h3 class="product-name">{p_name}</h3>
                <div class="price-box">
                    <span class="price-old">R$ {float(old_price):.2f}</span>
                    <span class="price-now">R$ {float(price):.2f}</span>
                </div>
                <a href="{product_url}" class="btn-buy" target="_blank" rel="noopener noreferrer">
                    🛒 Ir para a Loja
                </a>
            </div>
        </div>
        """
        
    # SEO e Metadados
    seo_title = f"{category_name} em Oferta | Radar de Preços - O Menor Preço Garantido"
    meta_description = f"Economize agora em {category_name}. Selecionamos as melhores ofertas do dia com descontos reais e links de afiliados seguros."
    canonical_url = f"{BASE_URL}categorias/{category_slug}/index.html"

    # Substituições no template
    page_content = template.replace("{{seo.title}}", seo_title)
    page_content = page_content.replace("{{meta.description}}", meta_description)
    page_content = page_content.replace("{{canonical.url}}", canonical_url)
    page_content = page_content.replace("{{category.name}}", category_name)
    page_content = page_content.replace("{{category.products}}", category_products_html)
    
    # Salvar página
    page_path = os.path.join(output_dir, category_slug, "index.html")
    os.makedirs(os.path.dirname(page_path), exist_ok=True)
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(page_content)
    logger.info(f"Página de categoria PREMIUM gerada: {page_path}")

def build_all_category_pages(input_path: str, template_path: str, output_dir: str) -> None:
    logger.info(f"Gerando páginas de categorias a partir de {input_path}...")
    
    if not os.path.exists(input_path):
        logger.error(f"Arquivo {input_path} não encontrado!")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        products = json.load(f)
        
    categories: Dict[str, List[Dict[str, Any]]] = {}
    
    for product in products:
        if product.get('status') != 'active': continue
        cat_slug = product.get("custom_category_slug", "outros")
        if cat_slug not in categories: categories[cat_slug] = []
        categories[cat_slug].append(product)
        
    # Marcas como categorias extras
    brands = ["samsung", "motorola", "lenovo", "lg", "jbl", "apple", "philco", "asus"]
    for product in products:
        if product.get('status') != 'active': continue
        name_lower = (product.get("name") or "").lower()
        for brand in brands:
            if brand in name_lower:
                if brand not in categories: categories[brand] = []
                categories[brand].append(product)
                break
        
    for slug, cat_products in categories.items():
        build_category_page(slug, cat_products, template_path, output_dir)

if __name__ == "__main__":
    build_all_category_pages("data/database/all_products.json", "templates/category_template.html", "categorias")
