import os
import json
import unicodedata
import random
from logger import logger

BASE_URL = "https://radardeprecos.github.io/radar/"

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().replace(' ', '-')
    return ''.join(c for c in text if c.isalnum() or c == '-')

def build_homepage(input_path: str, template_path: str, output_path: str) -> None:
    logger.info(f"Construindo página inicial dinâmica a partir de {input_path}...")
    if not os.path.exists(template_path):
        logger.error(f"Template {template_path} não encontrado!")
        return
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    products = []
    if os.path.exists(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {input_path}: {e}")
    
    if not products:
        logger.warning("Nenhum produto encontrado para a homepage.")
        return

    # Ordenar por desconto
    sorted_products = sorted(products, key=lambda x: x.get("custom_discount_pct", 0), reverse=True)
    
    # Selecionar o destaque (Hero Section)
    # ROTATIVIDADE AUMENTADA: Selecionamos aleatoriamente entre os TOP 30 produtos com maior desconto.
    # Isso garante que a cada execução do robô (a cada 2h), o destaque mude e não fique fixo em um só item.
    pool_size = min(len(sorted_products), 30)
    top_candidates = sorted_products[:pool_size]
    hero_product = random.choice(top_candidates)
    logger.info(f"Destaque rotativo escolhido: {hero_product.get('name')} (ID: {hero_product.get('id')})")
    
    # Remover o escolhido da lista para não repetir no grid logo abaixo
    remaining_products = [p for p in sorted_products if p['id'] != hero_product['id']]
    
    # Frases dinâmicas para o destaque
    badges = ["🔥 DESTAQUE DO DIA", "⚡ PREÇO BAIXOU!", "✨ NOVIDADE NO RADAR", "💎 ACHADO IMPERDÍVEL", "🚀 MELHOR DESCONTO"]
    catchy_phrases = [
        "Aproveite o maior desconto de hoje no Radar de Preços!",
        "Economize agora com esta oferta selecionada pelo nosso robô.",
        "Preço imbatível detectado! Confira os detalhes abaixo.",
        "Não perca essa oportunidade de pagar menos hoje.",
        "Oferta fresquinha saindo do forno para você."
    ]
    
    p = hero_product
    p_name = p.get("name") or p.get("title") or ""
    p_id = p.get("id", "")
    p_slug = slugify(p_name)
    p_cat = p.get("custom_category_slug", "outros")
    internal_url = f"ofertas/{p_cat}/{p_slug}-{p_id}.html"
    
    hero_html = f"""
    <div class="hero-content">
      <div class="hero-text">
        <span class="badge" style="background: var(--primary); color: white;">{random.choice(badges)}</span>
        <h1>{p_name}</h1>
        <p>{random.choice(catchy_phrases)}</p>
        <div class="price-tag" style="font-size: 32px;">R$ {p.get("price", 0):.2f} <span class="old-price" style="font-size: 18px;">R$ {p.get("originalPrice", 0):.2f}</span></div>
        <a href="{internal_url}" class="btn" style="padding: 15px 30px; font-size: 18px;">Ver Detalhes da Oferta</a>
      </div>
      <div class="hero-img">
        <img src="{p.get("image", p.get("thumbnail", ""))}" alt="{p_name}">
      </div>
    </div>
    """

    # Grid de produtos (Top 50 restantes)
    products_html = ""
    for idx, p in enumerate(remaining_products[:50]):
        p_name = p.get("name") or p.get("title") or ""
        p_id = p.get("id", "")
        p_slug = slugify(p_name)
        p_cat = p.get("custom_category_slug", "outros")
        internal_url = f"ofertas/{p_cat}/{p_slug}-{p_id}.html"
        discount = p.get("custom_discount_pct", 0)
        
        # Lógica de Selos Dinâmicos
        extra_badge = ""
        if discount >= 60:
            extra_badge = '<span class="badge badge-menor-preco">💎 MENOR PREÇO</span>'
        elif discount >= 45:
            extra_badge = '<span class="badge badge-baixou">📉 BAIXOU!</span>'
        elif idx < 5:
            extra_badge = '<span class="badge badge-promo-dia">🌟 PROMOÇÃO DO DIA</span>'
        
        products_html += f"""
        <div class="product-card" data-cat="{p_cat}">
            <span class="badge discount-badge">↓ {discount}% OFF</span>
            {extra_badge}
            <div class="card-img"><img src="{p.get("image", p.get("thumbnail", ""))}" alt="{p_name}"></div>
            <h3>{p_name[:50]}...</h3>
            <div class="price-tag">R$ {p.get("price", 0):.2f} <span class="old-price">R$ {p.get("originalPrice", 0):.2f}</span></div>
            <a href="{internal_url}" class="btn">Ver Oferta</a>
        </div>
        """
    
    seo_title = "Radar de Preços — As Melhores Ofertas do Mercado Livre Hoje"
    meta_description = "Economize com as melhores ofertas curadas do Mercado Livre. Descubra produtos com desconto de até 70% em eletrônicos, casa, beleza e muito mais."
    canonical_url = BASE_URL
    
    content = template.replace("{{seo.title}}", seo_title)
    content = content.replace("{{meta.description}}", meta_description)
    content = content.replace("{{canonical.url}}", canonical_url)
    content = content.replace("{{hero_section}}", hero_html)
    content = content.replace("{{featured_products_grid}}", products_html)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Homepage dinâmica gerada com sucesso: {output_path}")

if __name__ == "__main__":
    build_homepage("data/database/all_products.json", "templates/homepage.html", "index.html")
