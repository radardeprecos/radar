import os
import json
from typing import List, Dict, Any
from logger import logger

BASE_URL = "https://radardeprecos.github.io/radar/"

def slugify(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().replace(' ', '-')
    return ''.join(c for c in text if c.isalnum() or c == '-')

def generate_product_page(product: Dict[str, Any], template_path: str, output_dir: str) -> None:
    product_name = product.get('name') or product.get('title') or 'Produto'
    
    if not os.path.exists(template_path): 
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
        
    p_id = product.get('id', '0')
    p_slug = slugify(product_name)
    p_cat_slug = product.get('custom_category_slug', 'outros')
    
    # Formatação de preços
    try:
        price_val = float(product.get('price', 0))
        orig_val = float(product.get('originalPrice', 0))
    except (ValueError, TypeError):
        price_val = 0.0
        orig_val = 0.0
        
    p_price = f"R$ {price_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    p_orig = f"R$ {orig_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    p_img = product.get('image') or product.get('thumbnail') or ''
    
    # Lógica de URL Afiliada Corrigida
    _aff = product.get('custom_affiliate_url', '')
    _is_valid_aff = _aff and '/social/' not in _aff and 'vendas0nline?' not in _aff
    p_url = _aff if _is_valid_aff else (product.get('permalink') or '')
    
    p_discount = product.get('custom_discount_pct', 0)
    
    # Mapeamento de nomes de categorias
    cat_names = {
        "celulares": "Celulares",
        "informatica": "Informática",
        "eletrodomesticos": "Eletrodomésticos",
        "games": "Games",
        "tv-e-video": "TV e Vídeo",
        "ferramentas": "Ferramentas",
        "beleza": "Beleza",
        "casa": "Casa",
        "outros": "Outros"
    }
    p_cat_name = cat_names.get(p_cat_slug, p_cat_slug.title())
    
    # SEO DINÂMICO (Fase 1)
    seo_title = f"{product_name} com {p_discount}% de Desconto | Radar de Preços"
    meta_desc = f"Aproveite a oferta de {product_name} por apenas {p_price} no Mercado Livre. Economize {p_discount}% hoje no Radar de Preços!"
    canonical_url = f"{BASE_URL}ofertas/{p_cat_slug}/{p_slug}-{p_id}.html"
    
    # Substituições de Placeholders SEO
    content = template.replace('{{seo.title}}', seo_title)
    content = content.replace('{{meta.description}}', meta_desc)
    content = content.replace('{{canonical.url}}', canonical_url)
    
    # Substituições de Dados do Produto
    content = content.replace('{{product.name}}', product_name)
    content = content.replace('{{product.price}}', p_price)
    content = content.replace('{{product.price_raw}}', str(price_val)) # Para o Schema
    content = content.replace('{{product.originalPrice}}', p_orig)
    content = content.replace('{{product.image}}', p_img)
    content = content.replace('{{product.url}}', p_url)
    content = content.replace('{{product.id}}', p_id)
    content = content.replace('{{product.category}}', p_cat_slug)
    content = content.replace('{{product.category_name}}', p_cat_name)
    content = content.replace('{{product.discount}}', str(p_discount))
    
    # Descrição
    desc = product.get('description', f"Confira esta oferta incrível de {product_name} no Mercado Livre! Produto selecionado pelo Radar de Preços com o melhor desconto do dia.")
    content = content.replace('{{product.description_content}}', desc)
    
    path = os.path.join(output_dir, p_cat_slug, f'{p_slug}-{p_id}.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_all(input_p: str, temp_p: str, out_d: str) -> None:
    if not os.path.exists(input_p): 
        return
    try:
        with open(input_p, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao ler {input_p}: {e}")
        return
        
    logger.info(f"Gerando {len(products)} páginas de produtos com SEO otimizado...")
    for p in products:
        generate_product_page(p, temp_p, out_d)

if __name__ == '__main__':
    generate_all('data/new_offers.json', 'templates/product_template.html', 'ofertas')
