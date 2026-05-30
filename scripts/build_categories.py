import os
import json
from typing import List, Dict, Any
from logger import logger

def slugify(text: str) -> str:
    text = text.lower()
    text = text.replace(" ", "-")
    # BUGFIX: Corrigido "." para ""
    text = "".join(c for c in text if c.isalnum() or c == "-")
    return text

def build_category_page(category_slug: str, products: List[Dict[str, Any]], template_path: str, output_dir: str) -> None:
    logger.info(f"Gerando página para a categoria: {category_slug}")
    
    if not os.path.exists(template_path):
        logger.error(f"Template {template_path} não encontrado!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    category_name = category_slug.replace("-", " ").title()
    
    # Renderizar produtos da categoria
    category_products_html = ""
    for p in products:
        category_products_html += f"""
        <div class="product-card">
            <span class="badge">↓ {p.get("custom_discount_pct", 0)}%</span>
            <div class="card-img"><img src="{p.get("image", p.get("thumbnail", ""))}" alt="{p.get("name", "")}"></div>
            <h3>{p.get("name", "")[:50]}...</h3>
            <div class="price-tag" style="font-size: 20px;">R$ {p.get("price", 0):.2f}</div>
            <a href="{p.get('custom_affiliate_url', '') if p.get('custom_affiliate_url', '') and '/social/' not in p.get('custom_affiliate_url', '') and 'vendas0nline?' not in p.get('custom_affiliate_url', '') else p.get('permalink', '')}" class="btn" style="width: 100%; text-align: center;" target="_blank">Ver</a>
        </div>
        """
        
    # Substituições no template
    page_content = template.replace("{{category.name}}", category_name)
    page_content = page_content.replace("{{category.slug}}", category_slug)
    page_content = page_content.replace("{{category.products}}", category_products_html)
    
    # SEO para categorias
    seo_title = f"Ofertas de {category_name} com Desconto no Radar de Preços"
    meta_description = f"Encontre as melhores ofertas de {category_name} no Mercado Livre. Descontos incríveis e produtos selecionados para você economizar."
    page_content = page_content.replace("{{seo.title}}", seo_title)
    page_content = page_content.replace("{{meta.description}}", meta_description)
    
    # Salvar página
    page_path = os.path.join(output_dir, category_slug, "index.html")
    os.makedirs(os.path.dirname(page_path), exist_ok=True)
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(page_content)
    logger.info(f"Página de categoria gerada: {page_path}")

def build_all_category_pages(input_path: str, template_path: str, output_dir: str) -> None:
    logger.info(f"Gerando páginas de categorias a partir de {input_path}...")
    
    products = []
    if os.path.exists(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {input_path}: {e}")
    else:
        logger.warning(f"Arquivo de entrada {input_path} não encontrado!")
        
    if not products:
        logger.warning("Nenhum produto encontrado para gerar páginas de categorias.")
        return
        
    categories: Dict[str, List[Dict[str, Any]]] = {}
    for product in products:
        category_slug = product.get("custom_category_slug", "outros")
        if category_slug not in categories:
            categories[category_slug] = []
        categories[category_slug].append(product)
        
    for category_slug, cat_products in categories.items():
        try:
            build_category_page(category_slug, cat_products, template_path, output_dir)
        except Exception as e:
            logger.error(f"Erro ao gerar categoria {category_slug}: {e}")
        
    logger.info(f"Total de {len(categories)} páginas de categorias processadas.")

if __name__ == "__main__":
    try:
        build_all_category_pages("data/new_offers.json", "templates/category_template.html", "categorias")
    except Exception as e:
        logger.error(f"Erro fatal ao construir categorias: {e}")
