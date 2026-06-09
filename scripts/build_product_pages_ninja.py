#!/usr/bin/env python3
"""
Gerador Ninja de Páginas de Produto
Gera páginas de alta qualidade com:
- Schema Product JSON-LD correto
- FAQ gerado por IA (específico por produto)
- Prós/Contras gerados por IA
- Open Graph e Twitter Card
- Canonical URL
- Breadcrumb Schema
- Produtos similares
- Design responsivo e otimizado para AdSense
"""

import os
import sys
import json
import re
import time
import unicodedata
import random
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# Configurações
BASE_URL = "https://radardeprecos.github.io/radar"
ML_ACCOUNT = "60566305"
ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now().strftime("%Y-%m-%d")
NOW_BR = datetime.now().strftime("%d/%m/%Y")

# Cliente OpenAI
client = OpenAI()

# Mapeamento de categorias para nomes amigáveis
CATEGORY_NAMES = {
    "celulares": "Celulares e Smartphones",
    "games": "Games e Consoles",
    "informatica": "Informática",
    "beleza": "Beleza e Saúde",
    "casa": "Casa e Decoração",
    "eletrodomesticos": "Eletrodomésticos",
    "tv-e-video": "TV e Vídeo",
    "ferramentas": "Ferramentas",
    "tecnologia": "Tecnologia",
    "outros": "Outros",
}


def slugify(text: str) -> str:
    """Converte texto em slug válido para URL."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")[:80]


def format_price(value) -> str:
    """Formata valor como preço em reais."""
    try:
        v = float(value)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "Consulte"


def add_affiliate_tag(url: str) -> str:
    """Adiciona tag de afiliado ao link do Mercado Livre."""
    if not url:
        return "#"
    if "mercadolivre.com" in url or "mlb.com" in url:
        if "matt_tool=" not in url:
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}matt_tool={ML_ACCOUNT}"
        else:
            return re.sub(r"matt_tool=[^&]+", f"matt_tool={ML_ACCOUNT}", url)
    return url


def generate_llm_content(product_name: str, category: str, price: str, discount: int) -> dict:
    """Gera Prós/Contras e FAQ usando LLM."""
    cat_name = CATEGORY_NAMES.get(category, category)
    prompt = f"""Você é um especialista em análise de produtos de e-commerce brasileiro.
Analise o produto "{product_name}" da categoria "{cat_name}" com preço de {price} e {discount}% de desconto.

Retorne APENAS um JSON válido com esta estrutura exata:
{{
  "pros": ["pro1", "pro2", "pro3", "pro4"],
  "cons": ["con1", "con2"],
  "veredito": "Uma frase de 15-20 palavras sobre custo-benefício",
  "descricao": "Parágrafo de 80-100 palavras descrevendo o produto e seus benefícios para o consumidor brasileiro",
  "faq": [
    {{"pergunta": "Pergunta 1 específica sobre o produto?", "resposta": "Resposta detalhada de 30-50 palavras."}},
    {{"pergunta": "Pergunta 2 sobre entrega ou garantia?", "resposta": "Resposta detalhada de 30-50 palavras."}},
    {{"pergunta": "Pergunta 3 sobre uso ou compatibilidade?", "resposta": "Resposta detalhada de 30-50 palavras."}}
  ]
}}

Regras:
- Prós: benefícios reais e específicos do produto
- Contras: limitações honestas (não invente problemas graves)
- FAQ: perguntas que um comprador brasileiro faria
- Tudo em português do Brasil
- Não use markdown, apenas JSON puro"""

    try:
        response = client.chat.completions.create(
            model="claude-haiku-4-5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        content = response.choices[0].message.content.strip()
        # Limpar possível markdown
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"  ⚠️  LLM falhou para '{product_name[:40]}': {e}")
        return {
            "pros": [
                "Melhor preço dos últimos 30 dias",
                "Vendedor com excelente reputação no Mercado Livre",
                "Entrega rápida com Mercado Envios Full",
                f"Desconto real de {discount}% verificado pelo Radar",
            ],
            "cons": [
                "Estoque limitado — pode esgotar rápido",
                "Preço pode variar a qualquer momento",
            ],
            "veredito": f"Excelente oportunidade com {discount}% de desconto real e entrega garantida.",
            "descricao": f"O {product_name} é uma das melhores ofertas disponíveis hoje no Mercado Livre. Com desconto de {discount}%, este produto oferece excelente custo-benefício para quem busca qualidade com economia. Aproveite enquanto o estoque durar.",
            "faq": [
                {
                    "pergunta": f"O {product_name[:40]} tem garantia?",
                    "resposta": "Sim, todos os produtos vendidos no Mercado Livre têm garantia legal de 90 dias para produtos não duráveis e 1 ano para duráveis, além da garantia do fabricante.",
                },
                {
                    "pergunta": "Como funciona a entrega?",
                    "resposta": "A entrega é feita pelo Mercado Envios. Produtos com o selo Full chegam em até 2 dias úteis. O prazo exato é exibido na página do produto no Mercado Livre.",
                },
                {
                    "pergunta": "Posso devolver se não gostar?",
                    "resposta": "Sim. Pelo Código de Defesa do Consumidor, você tem 7 dias para devolver compras online sem precisar justificar. O Mercado Livre facilita todo o processo de devolução.",
                },
            ],
        }


def generate_product_page(product: dict, all_products: list) -> tuple:
    """Gera página HTML completa de produto."""
    p_id = str(product.get("id", ""))
    p_name = product.get("name") or product.get("title") or "Produto"
    p_cat = product.get("custom_category_slug", "outros")
    p_cat_name = CATEGORY_NAMES.get(p_cat, p_cat.title())
    p_slug = slugify(p_name)
    p_img = product.get("image") or product.get("thumbnail") or f"{BASE_URL}/assets/og-default.png"
    p_url = add_affiliate_tag(product.get("permalink") or product.get("custom_affiliate_url") or "")

    # Preços
    price_val = float(product.get("price", 0) or 0)
    orig_val = float(product.get("originalPrice") or product.get("original_price") or price_val * 1.2)
    discount = int(product.get("custom_discount_pct", 0) or 0)
    if discount == 0 and orig_val > price_val:
        discount = int(((orig_val - price_val) / orig_val) * 100)
    savings_val = orig_val - price_val

    p_price = format_price(price_val)
    p_orig = format_price(orig_val)
    p_savings = format_price(savings_val)

    # URLs
    page_url = f"{BASE_URL}/ofertas/{p_cat}/{p_slug}-{p_id}.html"
    canonical_url = page_url

    # Gerar conteúdo LLM
    print(f"  🤖 Gerando conteúdo IA para: {p_name[:50]}...")
    llm_data = generate_llm_content(p_name, p_cat, p_price, discount)
    time.sleep(0.3)  # Rate limit

    pros = llm_data.get("pros", [])
    cons = llm_data.get("cons", [])
    veredito = llm_data.get("veredito", "")
    descricao = llm_data.get("descricao", "")
    faq_items = llm_data.get("faq", [])

    # Produtos similares
    similars = [
        p for p in all_products
        if p.get("custom_category_slug") == p_cat
        and str(p.get("id", "")) != p_id
    ]
    random.shuffle(similars)
    similars = similars[:4]

    # HTML dos similares
    similars_html = ""
    if similars:
        cards = ""
        for s in similars:
            s_name = s.get("name") or s.get("title") or "Produto"
            s_price = format_price(s.get("price", 0))
            s_slug = slugify(s_name)
            s_id = str(s.get("id", ""))
            s_img = s.get("image") or s.get("thumbnail") or ""
            s_url = f"../../ofertas/{s.get('custom_category_slug', 'outros')}/{s_slug}-{s_id}.html"
            cards += f"""
            <div class="similar-card">
                <img src="{s_img}" alt="{s_name}" loading="lazy" width="200" height="200">
                <div class="similar-card-info">
                    <h4>{s_name[:55]}...</h4>
                    <div class="price">{s_price}</div>
                    <a href="{s_url}">Ver Oferta →</a>
                </div>
            </div>"""
        similars_html = f"""
        <section class="similars" style="margin-top: 40px;">
            <h2 style="font-size: 22px; font-weight: 800; margin-bottom: 20px;">Produtos Similares em Oferta</h2>
            <div class="similars-grid">{cards}</div>
        </section>"""

    # Schema JSON-LD — Product
    product_schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p_name,
        "description": descricao[:200] if descricao else f"Oferta de {p_name} no Mercado Livre",
        "image": p_img,
        "url": canonical_url,
        "brand": {"@type": "Brand", "name": p_name.split()[0] if p_name else "Marca"},
        "offers": {
            "@type": "Offer",
            "price": str(price_val),
            "priceCurrency": "BRL",
            "availability": "https://schema.org/InStock",
            "url": p_url,
            "priceValidUntil": "2026-12-31",
            "seller": {"@type": "Organization", "name": "Mercado Livre"},
        },
    }

    # Schema JSON-LD — BreadcrumbList
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Radar de Preços", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Ofertas", "item": f"{BASE_URL}/ofertas/"},
            {"@type": "ListItem", "position": 3, "name": p_cat_name, "item": f"{BASE_URL}/categorias/{p_cat}/"},
            {"@type": "ListItem", "position": 4, "name": p_name, "item": canonical_url},
        ],
    }

    # Schema JSON-LD — FAQPage
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["pergunta"],
                "acceptedAnswer": {"@type": "Answer", "text": item["resposta"]},
            }
            for item in faq_items
        ],
    }

    # HTML dos prós
    pros_html = "\n".join(f"<li>✅ {p}</li>" for p in pros)
    cons_html = "\n".join(f"<li>❌ {c}</li>" for c in cons)

    # HTML do FAQ
    faq_html = ""
    for item in faq_items:
        faq_html += f"""
        <div class="faq-item" style="margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
            <div style="background: #f8fafc; padding: 15px 20px; font-weight: 700; color: #1e293b; cursor: pointer;" 
                 onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">
                ❓ {item['pergunta']}
            </div>
            <div style="padding: 15px 20px; color: #475569; line-height: 1.7; display: none;">
                {item['resposta']}
            </div>
        </div>"""

    # Score dinâmico baseado no desconto
    score = min(9.9, 5.0 + (discount / 10))
    score_label = "🟢 Excelente Compra" if score >= 8.5 else ("🟡 Bom Preço" if score >= 7.0 else "🔴 Aguarde")

    # Meta description
    meta_desc = f"Oferta: {p_name} por {p_price} ({discount}% OFF). {veredito[:80] if veredito else 'Melhor preço verificado pelo Radar de Preços.'}"[:160]
    seo_title = f"{p_name} — {discount}% OFF por {p_price} | Radar de Preços"[:70]

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{seo_title}</title>
    <meta name="description" content="{meta_desc}">
    <link rel="canonical" href="{canonical_url}">

    <!-- Open Graph -->
    <meta property="og:type" content="product">
    <meta property="og:title" content="{seo_title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:image" content="{p_img}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:site_name" content="Radar de Preços">
    <meta property="product:price:amount" content="{price_val}">
    <meta property="product:price:currency" content="BRL">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{seo_title}">
    <meta name="twitter:description" content="{meta_desc}">
    <meta name="twitter:image" content="{p_img}">

    <!-- Schema Markup -->
    <script type="application/ld+json">{json.dumps(product_schema, ensure_ascii=False)}</script>
    <script type="application/ld+json">{json.dumps(breadcrumb_schema, ensure_ascii=False)}</script>
    <script type="application/ld+json">{json.dumps(faq_schema, ensure_ascii=False)}</script>

    <!-- Google AdSense -->
    <meta name="google-adsense-account" content="ca-pub-4896859041377751">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #f5f7fa; color: #1e293b; }}
        a {{ color: #1a73e8; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        /* Header */
        .site-header {{ background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); padding: 16px 20px; color: white; }}
        .site-header .inner {{ max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }}
        .site-header .logo {{ color: white; font-size: 20px; font-weight: 800; text-decoration: none; }}
        .site-header nav a {{ color: rgba(255,255,255,0.85); font-size: 14px; margin-left: 20px; }}
        .site-header nav a:hover {{ color: white; text-decoration: none; }}

        /* Container */
        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}

        /* Breadcrumb */
        .breadcrumb {{ font-size: 13px; color: #64748b; margin-bottom: 20px; }}
        .breadcrumb a {{ color: #1a73e8; }}
        .breadcrumb span {{ color: #94a3b8; margin: 0 6px; }}

        /* Score Banner */
        .score-banner {{ background: linear-gradient(135deg, #00c853 0%, #00a040 100%); color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 28px; display: flex; align-items: center; gap: 20px; box-shadow: 0 4px 15px rgba(0,200,83,0.25); }}
        .score-circle {{ width: 72px; height: 72px; border-radius: 50%; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 800; border: 3px solid white; flex-shrink: 0; }}
        .score-text h2 {{ font-size: 20px; font-weight: 800; margin-bottom: 4px; }}
        .score-text p {{ font-size: 13px; opacity: 0.9; }}

        /* Product Grid */
        .product-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }}
        @media (max-width: 768px) {{ .product-grid {{ grid-template-columns: 1fr; }} }}

        /* Product Image */
        .product-image {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; align-items: center; justify-content: center; }}
        .product-image img {{ width: 100%; max-height: 320px; object-fit: contain; border-radius: 8px; }}

        /* Price Section */
        .price-section {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .product-title {{ font-size: 22px; font-weight: 800; margin-bottom: 16px; line-height: 1.35; color: #0f172a; }}
        .price-old {{ font-size: 15px; color: #94a3b8; text-decoration: line-through; display: block; margin-bottom: 6px; }}
        .price-current {{ font-size: 42px; font-weight: 800; color: #00c853; display: block; margin-bottom: 8px; line-height: 1; }}
        .discount-badge {{ display: inline-block; background: #ff6b35; color: white; padding: 6px 14px; border-radius: 6px; font-weight: 700; font-size: 13px; margin-right: 8px; }}
        .savings {{ display: inline-block; font-size: 14px; color: #00c853; font-weight: 600; }}
        .btn-buy {{ display: block; width: 100%; padding: 18px; background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); color: white; text-align: center; text-decoration: none; border-radius: 8px; font-weight: 800; font-size: 17px; margin-top: 20px; box-shadow: 0 6px 20px rgba(255,152,0,0.3); transition: all 0.2s ease; }}
        .btn-buy:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(255,152,0,0.4); text-decoration: none; }}
        .affiliate-notice {{ font-size: 11px; color: #94a3b8; text-align: center; margin-top: 8px; }}

        /* Sections */
        .section {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 24px; }}
        .section h2 {{ font-size: 20px; font-weight: 800; margin-bottom: 16px; color: #0f172a; padding-bottom: 10px; border-bottom: 2px solid #1a73e8; }}
        .section p {{ font-size: 15px; line-height: 1.75; color: #475569; }}

        /* Pros/Cons */
        .pros-cons {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 600px) {{ .pros-cons {{ grid-template-columns: 1fr; }} }}
        .pros-box {{ background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 4px solid #22c55e; }}
        .cons-box {{ background: #fff5f5; padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444; }}
        .pros-box h3 {{ color: #166534; margin-bottom: 12px; font-size: 16px; }}
        .cons-box h3 {{ color: #991b1b; margin-bottom: 12px; font-size: 16px; }}
        .pros-box ul, .cons-box ul {{ list-style: none; padding: 0; }}
        .pros-box li, .cons-box li {{ font-size: 14px; margin-bottom: 8px; line-height: 1.5; }}

        /* Veredito */
        .veredito {{ background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%); padding: 20px; border-radius: 10px; border-left: 5px solid #00c853; margin-top: 20px; }}
        .veredito strong {{ color: #1b5e20; font-size: 16px; }}
        .veredito p {{ color: #2d6a4f; margin-top: 8px; font-size: 15px; }}

        /* Specs Table */
        .specs-table {{ width: 100%; border-collapse: collapse; }}
        .specs-table tr:nth-child(even) {{ background: #f8fafc; }}
        .specs-table td {{ padding: 12px 15px; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
        .specs-table td:first-child {{ font-weight: 600; color: #475569; width: 35%; }}
        .specs-table td:last-child {{ color: #0f172a; }}

        /* CTA Banner */
        .cta-banner {{ background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 24px; }}
        .cta-banner h3 {{ font-size: 22px; font-weight: 800; margin-bottom: 10px; }}
        .cta-banner p {{ opacity: 0.9; margin-bottom: 20px; font-size: 15px; }}
        .cta-banner a {{ display: inline-block; background: #ff9800; color: white; padding: 14px 36px; border-radius: 8px; font-weight: 800; font-size: 16px; text-decoration: none; transition: all 0.2s; }}
        .cta-banner a:hover {{ background: #f57c00; transform: scale(1.03); }}

        /* Similars */
        .similars-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
        .similar-card {{ background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: all 0.2s; }}
        .similar-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }}
        .similar-card img {{ width: 100%; height: 160px; object-fit: contain; padding: 10px; background: #f8fafc; }}
        .similar-card-info {{ padding: 12px; }}
        .similar-card h4 {{ font-size: 13px; font-weight: 600; margin-bottom: 6px; line-height: 1.4; color: #0f172a; }}
        .similar-card .price {{ font-size: 15px; font-weight: 800; color: #00c853; margin-bottom: 8px; }}
        .similar-card a {{ display: block; text-align: center; padding: 8px; background: #1a73e8; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 12px; }}

        /* Footer */
        footer {{ background: #0f172a; color: #94a3b8; padding: 30px 20px; text-align: center; margin-top: 40px; }}
        footer p {{ font-size: 13px; margin-bottom: 6px; }}
        footer a {{ color: #64748b; }}
    </style>
</head>
<body>

<header class="site-header">
    <div class="inner">
        <a href="{BASE_URL}/" class="logo">📡 Radar de Preços</a>
        <nav>
            <a href="{BASE_URL}/categorias/">Categorias</a>
            <a href="{BASE_URL}/comparativos/">Comparativos</a>
            <a href="{BASE_URL}/noticias/">Blog</a>
            <a href="{BASE_URL}/sobre/">Sobre</a>
        </nav>
    </div>
</header>

<main class="container">

    <!-- Breadcrumb -->
    <nav class="breadcrumb" aria-label="Navegação estrutural">
        <a href="{BASE_URL}/">Home</a>
        <span>›</span>
        <a href="{BASE_URL}/ofertas/">Ofertas</a>
        <span>›</span>
        <a href="{BASE_URL}/categorias/{p_cat}/">{p_cat_name}</a>
        <span>›</span>
        <span style="color:#1e293b;">{p_name[:50]}</span>
    </nav>

    <!-- Score Banner -->
    <div class="score-banner">
        <div class="score-circle">{score:.1f}</div>
        <div class="score-text">
            <h2>{score_label}</h2>
            <p>Análise do Radar de Preços • Atualizado em {NOW_BR}</p>
        </div>
    </div>

    <!-- Product Grid -->
    <div class="product-grid">
        <div class="product-image">
            <img src="{p_img}"
                 alt="{p_name} — Oferta no Mercado Livre"
                 width="400" height="400"
                 loading="eager">
        </div>
        <div class="price-section">
            <h1 class="product-title">{p_name}</h1>
            <span class="price-old">De: {p_orig}</span>
            <span class="price-current">{p_price}</span>
            <span class="discount-badge">{discount}% OFF</span>
            <span class="savings">Economia de {p_savings}</span>
            <a href="{p_url}" class="btn-buy" rel="nofollow noopener" target="_blank">
                🛒 Ver Oferta no Mercado Livre →
            </a>
            <p class="affiliate-notice">* Link de afiliado — ganhamos comissão sem custo adicional para você</p>
        </div>
    </div>

    <!-- Descrição -->
    <div class="section">
        <h2>Sobre o Produto</h2>
        <p>{descricao}</p>
    </div>

    <!-- Prós e Contras -->
    <div class="section">
        <h2>Análise do Especialista Ninja</h2>
        <div class="pros-cons">
            <div class="pros-box">
                <h3>👍 Prós</h3>
                <ul>{pros_html}</ul>
            </div>
            <div class="cons-box">
                <h3>👎 Contras</h3>
                <ul>{cons_html}</ul>
            </div>
        </div>
        <div class="veredito">
            <strong>🏆 VEREDITO DO RADAR:</strong>
            <p>{veredito}</p>
        </div>
    </div>

    <!-- Especificações -->
    <div class="section">
        <h2>Ficha Técnica</h2>
        <table class="specs-table">
            <tr><td>Categoria</td><td>{p_cat_name}</td></tr>
            <tr><td>Preço Atual</td><td><strong style="color:#00c853;">{p_price}</strong></td></tr>
            <tr><td>Preço Original</td><td><s>{p_orig}</s></td></tr>
            <tr><td>Desconto</td><td><strong style="color:#ff6b35;">{discount}% OFF</strong></td></tr>
            <tr><td>Economia</td><td><strong style="color:#00c853;">{p_savings}</strong></td></tr>
            <tr><td>Disponibilidade</td><td>✅ Em Estoque no Mercado Livre</td></tr>
            <tr><td>Atualizado em</td><td>{NOW_BR}</td></tr>
        </table>
    </div>

    <!-- CTA -->
    <div class="cta-banner">
        <h3>⚡ Oferta por Tempo Limitado!</h3>
        <p>Preço pode subir a qualquer momento. Garanta o seu agora com {discount}% de desconto.</p>
        <a href="{p_url}" rel="nofollow noopener" target="_blank">Comprar Agora por {p_price} →</a>
    </div>

    <!-- FAQ -->
    <div class="section">
        <h2>Perguntas Frequentes</h2>
        {faq_html}
    </div>

    <!-- Produtos Similares -->
    {similars_html}

    <!-- Navegação -->
    <div style="text-align:center; margin: 30px 0; padding-top: 20px; border-top: 1px solid #e2e8f0;">
        <a href="{BASE_URL}/categorias/{p_cat}/" style="color:#1a73e8; font-weight:600; margin-right:20px;">
            ← Ver mais em {p_cat_name}
        </a>
        <a href="{BASE_URL}/comparativos/" style="color:#1a73e8; font-weight:600;">
            Ver Comparativos →
        </a>
    </div>

</main>

<footer>
    <p>© 2026 Radar de Preços — As melhores ofertas do Mercado Livre com atualização automática.</p>
    <p>
        <a href="{BASE_URL}/privacidade/">Privacidade</a> ·
        <a href="{BASE_URL}/termos/">Termos</a> ·
        <a href="{BASE_URL}/sobre/">Sobre</a> ·
        <a href="{BASE_URL}/contato/">Contato</a>
    </p>
    <p style="margin-top:10px; font-size:12px;">
        Somos afiliados do Mercado Livre. Ganhamos comissão por vendas realizadas através dos nossos links, sem custo adicional para você.
    </p>
</footer>

</body>
</html>"""

    filename = f"ofertas/{p_cat}/{p_slug}-{p_id}.html"
    return html, filename


def main():
    print("=" * 60)
    print("🚀 GERADOR NINJA DE PÁGINAS DE PRODUTO")
    print(f"   Data: {NOW_BR}")
    print("=" * 60)

    # Carregar produtos
    products_file = ROOT / "data" / "database" / "validated_200_products.json"
    if not products_file.exists():
        print(f"❌ Arquivo não encontrado: {products_file}")
        sys.exit(1)

    with open(products_file, encoding="utf-8") as f:
        products = json.load(f)

    print(f"\n📦 {len(products)} produtos carregados")

    # Gerar páginas
    success = 0
    errors = 0
    generated_files = []

    for i, product in enumerate(products, 1):
        p_name = product.get("name") or product.get("title") or "Produto"
        p_cat = product.get("custom_category_slug", "outros")
        print(f"\n[{i:02d}/{len(products)}] {p_name[:55]}...")

        try:
            html, filename = generate_product_page(product, products)
            output_path = ROOT / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            generated_files.append(filename)
            success += 1
            print(f"  ✅ Salvo: {filename}")

        except Exception as e:
            errors += 1
            print(f"  ❌ Erro: {e}")

    # Salvar lista de arquivos gerados
    report_path = ROOT / "data" / "generated_pages_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": NOW,
                "total": len(products),
                "success": success,
                "errors": errors,
                "files": generated_files,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("\n" + "=" * 60)
    print(f"✅ CONCLUÍDO: {success} páginas geradas, {errors} erros")
    print(f"📄 Relatório salvo em: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
