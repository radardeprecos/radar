import os
import json
from typing import List, Dict, Any
from logger import logger

def slugify(text: str) -> str:
    text = text.lower()
    text = text.replace(" ", "-")
    text = ''.join(c for c in text if c.isalnum() or c == '-')
    return text

def generate_product_page(product: Dict[str, Any], template_path: str, output_dir: str) -> None:
    # BUGFIX: Corrigido SyntaxError nas aspas da f-string
    name = product.get("name") or product.get("title") or "Produto"
    logger.info(f"Gerando página para o produto: {name}")
    
    if not os.path.exists(template_path):
        logger.error(f"Template {template_path} não encontrado!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    # Preparar dados para o template
    product_name = name
    product_slug = slugify(product_name)
    product_id = product.get("id", "")
    
    # Garantir que os campos numéricos existam
    price_val = product.get("price", 0) or 0
    orig_price_val = product.get("originalPrice") or product.get("original_price") or price_val
    
    product_price = f"R$ {float(price_val):.2f}".replace(".", ",")
    product_original_price = f"R$ {float(orig_price_val):.2f}".replace(".", ",")
    product_discount = product.get("custom_discount_pct", 0)
    product_image = product.get("custom_image_url", "")
    product_url = product.get("custom_affiliate_url", "")
    product_category = product.get("custom_category_slug", "")
    product_permalink = product.get("permalink", "")
    
    # Conteúdo SEO e descrição
    seo_title = f"{product_name} com {product_discount}% OFF no Radar de Preços"
    meta_description = f"Encontre {product_name} com {product_discount}% de desconto. Compare preços e aproveite as melhores ofertas do Mercado Livre no Radar de Preços."
    description_content = f"<p>Aproveite a oferta imperdível do {product_name} no Mercado Livre! Com um desconto de {product_discount}%, este é o momento perfeito para adquirir este produto de alta qualidade. O {product_name} oferece uma experiência excepcional, combinando desempenho e durabilidade. Não perca tempo, clique no botão 'Ver oferta' e garanta já o seu!</p>\n<p>Este produto é ideal para quem busca {product_category} com o melhor custo-benefício. Sua tecnologia avançada garante que você terá um item moderno e eficiente. Além disso, a compra é segura e o envio rápido, direto do Mercado Livre para sua casa.</p>\n<p>Fique atento às nossas atualizações diárias para não perder nenhuma promoção. O Radar de Preços está sempre buscando as melhores oportunidades para você economizar.</p>"
    
    # Substituições no template
    page_content = template.replace("{{product.name}}", product_name)
    page_content = page_content.replace("{{product.id}}", product_id)
    page_content = page_content.replace("{{product.price}}", product_price)
    page_content = page_content.replace("{{product.originalPrice}}", product_original_price)
    page_content = page_content.replace("{{product.discount}}", str(product_discount))
    page_content = page_content.replace("{{product.image}}", product_image)
    page_content = page_content.replace("{{product.url}}", product_url)
    page_content = page_content.replace("{{product.category}}", product_category.replace("-", " ").title())
    page_content = page_content.replace("{{product.permalink}}", product_permalink)
    page_content = page_content.replace("{{seo.title}}", seo_title)
    page_content = page_content.replace("{{meta.description}}", meta_description)
    page_content = page_content.replace("{{product.description_content}}", description_content)
    
    # Salvar página
    page_path = os.path.join(output_dir, product_category, f"{product_slug}-{product_id}.html")
    os.makedirs(os.path.dirname(page_path), exist_ok=True)
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(page_content)
    logger.info(f"Página gerada: {page_path}")

def generate_all_product_pages(input_path: str, template_path: str, output_dir: str) -> None:
    logger.info(f"Gerando páginas de produtos a partir de {input_path}...")
    if not os.path.exists(input_path):
        logger.warning(f"Arquivo de entrada {input_path} não encontrado. Nenhuma página será gerada.")
        return
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler {input_path}: {e}")
        return
        
    if not products:
        logger.warning("Nenhum produto encontrado para gerar páginas.")
        return
        
    for product in products:
        try:
            generate_product_page(product, template_path, output_dir)
        except Exception as e:
            logger.error(f"Erro ao gerar página para produto {product.get('id')}: {e}")
        
    logger.info(f"Total de {len(products)} páginas de produtos processadas.")

if __name__ == "__main__":
    try:
        generate_all_product_pages("data/new_offers.json", "templates/product_template.html", "ofertas")
    except Exception as e:
        logger.error(f"Erro fatal no gerador de páginas: {e}")
        # Hardening: Não sair com erro para não quebrar o workflow
