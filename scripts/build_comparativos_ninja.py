#!/usr/bin/env python3
"""
Gerador Ninja de Comparativos de Alta Intenção
Cria páginas "Produto A vs Produto B" com análise detalhada por IA.
Foco em comparações dentro da mesma categoria (alta intenção de compra).
"""

import os
import sys
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# Configurações
BASE_URL = "https://radardeprecos.github.io/radar"
ML_ACCOUNT = "60566305"
ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now().strftime("%Y-%m-%d")
NOW_BR = datetime.now().strftime("%d/%m/%Y")

client = OpenAI()

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
}

# Pares de comparação de alta intenção (mesma categoria)
HIGH_INTENT_PAIRS = [
    # Celulares
    ("Samsung Galaxy A17 5G 128GB", "Smartphone Motorola Moto G35 5G"),
    ("Samsung Galaxy A36 5G 128GB", "Smartphone Samsung Galaxy A17 5G"),
    ("Samsung Galaxy A07 256GB 8GB", "Samsung Galaxy A06 5G 128GB"),
    ("Celular Samsung Galaxy A17 Com Ia, 256gb", "Samsung Galaxy A17 5G 128GB"),
    ("Smartphone Samsung Galaxy S23 FE 256GB", "Samsung Galaxy A36 5G 128GB"),
    # Games
    ("Console Playstation 5 Slim Edição Digital", "Asus ROG Ally Z1 Extreme 512GB"),
    ("Controle DualSense PS5 Branco Original", "Headset Gamer HyperX Cloud Stinger Core"),
    # Informática
    ("Monitor Gamer LG Ultragear 24 180Hz", "Monitor Gamer LG Ultragear 24 24gs60f-b"),
    ("Teclado Mecânico Gamer Redragon Kumara", "Mouse Sem Fio Logitech M170"),
    # TV
    ("Smart TV Samsung 32 LS32H5000", "Smart TV Philco 40 P40VIK"),
    ("Smart TV LG UHD AI UA75 65 Polegadas", "Smart TV Philco 58 P58VIK 4K"),
    # Beleza/Saúde
    ("Whey Protein Concentrado 100% 900g Dark Lab", "Creatina Monohidratada Pura 1kg Dark Lab"),
    ("Creatina Monohidratada 250g Growth Supplements", "Creatina Monohidratada Pura 500g Dark Lab"),
    # Eletrodomésticos
    ("Fritadeira Air Fryer Mondial 4L Inox AF-31", "Cooktop A Gás Fischer 4 Bocas Fit Line"),
    ("Chuveiro Eletrônico Lorenzetti Acqua Duo Ultra", "Caixa De Som Boombox Aiwa 200W"),
]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")[:60]


def format_price(value) -> str:
    try:
        v = float(value)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "Consulte"


def add_affiliate_tag(url: str) -> str:
    if not url:
        return "#"
    if "mercadolivre.com" in url or "mlb.com" in url:
        if "matt_tool=" not in url:
            sep = "&" if "?" in url else "?"
            return f"{url}{sep}matt_tool={ML_ACCOUNT}"
        else:
            return re.sub(r"matt_tool=[^&]+", f"matt_tool={ML_ACCOUNT}", url)
    return url


def find_product(products: list, name_query: str) -> dict | None:
    """Encontra produto pelo nome (busca fuzzy)."""
    name_lower = name_query.lower()
    # Busca exata primeiro
    for p in products:
        pname = (p.get("name") or p.get("title") or "").lower()
        if name_lower in pname or pname in name_lower:
            return p
    # Busca por palavras-chave
    words = name_lower.split()[:4]
    best_match = None
    best_score = 0
    for p in products:
        pname = (p.get("name") or p.get("title") or "").lower()
        score = sum(1 for w in words if w in pname)
        if score > best_score:
            best_score = score
            best_match = p
    return best_match if best_score >= 2 else None


def generate_comparison_analysis(p1_name: str, p2_name: str, p1_price: str, p2_price: str, category: str) -> dict:
    """Gera análise comparativa usando LLM."""
    cat_name = CATEGORY_NAMES.get(category, category)
    prompt = f"""Compare os produtos "{p1_name}" e "{p2_name}" da categoria "{cat_name}".
{p1_name} custa {p1_price} e {p2_name} custa {p2_price}.

Retorne APENAS um JSON válido:
{{
  "resumo": "Parágrafo de 60-80 palavras explicando as diferenças principais",
  "vencedor": "nome do produto que oferece melhor custo-benefício",
  "motivo_vencedor": "frase de 15-20 palavras explicando por que vence",
  "p1_pros": ["vantagem1", "vantagem2", "vantagem3"],
  "p2_pros": ["vantagem1", "vantagem2", "vantagem3"],
  "recomendacao_p1": "Para quem é ideal o {p1_name} (20 palavras)",
  "recomendacao_p2": "Para quem é ideal o {p2_name} (20 palavras)",
  "faq": [
    {{"pergunta": "Qual a principal diferença entre os dois?", "resposta": "Resposta de 30-40 palavras."}},
    {{"pergunta": "Qual tem melhor custo-benefício?", "resposta": "Resposta de 30-40 palavras."}}
  ]
}}"""

    try:
        response = client.chat.completions.create(
            model="claude-haiku-4-5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=900,
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        return json.loads(content)
    except Exception as e:
        print(f"  ⚠️  LLM falhou: {e}")
        return {
            "resumo": f"Comparativo entre {p1_name} e {p2_name}. Ambos são excelentes opções na categoria {cat_name}. A escolha ideal depende do seu orçamento e necessidades específicas.",
            "vencedor": p1_name if True else p2_name,
            "motivo_vencedor": "Melhor relação entre preço, qualidade e recursos disponíveis.",
            "p1_pros": ["Boa relação custo-benefício", "Disponível no Mercado Livre", "Entrega rápida"],
            "p2_pros": ["Boa relação custo-benefício", "Disponível no Mercado Livre", "Entrega rápida"],
            "recomendacao_p1": f"Ideal para quem busca {p1_name[:30]} com bom preço.",
            "recomendacao_p2": f"Ideal para quem busca {p2_name[:30]} com bom preço.",
            "faq": [
                {"pergunta": "Qual a principal diferença entre os dois?", "resposta": "Os dois produtos têm características distintas. Avalie preço, especificações e avaliações antes de decidir."},
                {"pergunta": "Qual tem melhor custo-benefício?", "resposta": "Depende do seu uso. Verifique os preços atuais no Mercado Livre para tomar a melhor decisão."},
            ],
        }


def generate_comparison_page(p1: dict, p2: dict) -> tuple:
    """Gera página HTML de comparativo."""
    p1_name = p1.get("name") or p1.get("title") or "Produto 1"
    p2_name = p2.get("name") or p2.get("title") or "Produto 2"
    p1_cat = p1.get("custom_category_slug", "outros")
    p2_cat = p2.get("custom_category_slug", "outros")
    category = p1_cat  # Usar categoria do primeiro produto

    p1_price_val = float(p1.get("price", 0) or 0)
    p2_price_val = float(p2.get("price", 0) or 0)
    p1_price = format_price(p1_price_val)
    p2_price = format_price(p2_price_val)

    p1_orig = format_price(p1.get("originalPrice") or p1.get("original_price") or p1_price_val * 1.2)
    p2_orig = format_price(p2.get("originalPrice") or p2.get("original_price") or p2_price_val * 1.2)

    p1_discount = int(p1.get("custom_discount_pct", 0) or 0)
    p2_discount = int(p2.get("custom_discount_pct", 0) or 0)

    p1_img = p1.get("image") or p1.get("thumbnail") or f"{BASE_URL}/assets/og-default.png"
    p2_img = p2.get("image") or p2.get("thumbnail") or f"{BASE_URL}/assets/og-default.png"

    p1_url = add_affiliate_tag(p1.get("permalink") or p1.get("custom_affiliate_url") or "")
    p2_url = add_affiliate_tag(p2.get("permalink") or p2.get("custom_affiliate_url") or "")

    p1_id = str(p1.get("id", ""))
    p2_id = str(p2.get("id", ""))

    # Slugs para links internos
    p1_slug = slugify(p1_name)
    p2_slug = slugify(p2_name)
    p1_page = f"{BASE_URL}/ofertas/{p1_cat}/{p1_slug}-{p1_id}.html"
    p2_page = f"{BASE_URL}/ofertas/{p2_cat}/{p2_slug}-{p2_id}.html"

    # Gerar análise LLM
    print(f"  🤖 Gerando análise comparativa...")
    analysis = generate_comparison_analysis(p1_name, p2_name, p1_price, p2_price, category)
    time.sleep(0.3)

    # Determinar vencedor
    winner_name = analysis.get("vencedor", p1_name)
    is_p1_winner = p1_name.lower() in winner_name.lower() or winner_name.lower() in p1_name.lower()

    # Slug da página de comparativo
    comp_slug = f"{slugify(p1_name)}-vs-{slugify(p2_name)}"
    page_url = f"{BASE_URL}/comparativos/{comp_slug}.html"

    # Título e meta
    seo_title = f"{p1_name[:35]} vs {p2_name[:35]} — Qual o Melhor? | Radar de Preços"
    meta_desc = f"Compare {p1_name[:40]} ({p1_price}) vs {p2_name[:40]} ({p2_price}). Análise completa de prós, contras e custo-benefício."[:160]

    # Schema
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Radar de Preços", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Comparativos", "item": f"{BASE_URL}/comparativos/"},
            {"@type": "ListItem", "position": 3, "name": f"{p1_name[:30]} vs {p2_name[:30]}", "item": page_url},
        ],
    }

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["pergunta"],
                "acceptedAnswer": {"@type": "Answer", "text": item["resposta"]},
            }
            for item in analysis.get("faq", [])
        ],
    }

    # HTML dos prós
    p1_pros_html = "\n".join(f"<li>✅ {p}</li>" for p in analysis.get("p1_pros", []))
    p2_pros_html = "\n".join(f"<li>✅ {p}</li>" for p in analysis.get("p2_pros", []))

    # FAQ HTML
    faq_html = ""
    for item in analysis.get("faq", []):
        faq_html += f"""
        <div class="faq-item">
            <div class="faq-q" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">
                ❓ {item['pergunta']}
            </div>
            <div class="faq-a" style="display:none;">
                {item['resposta']}
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{seo_title}</title>
    <meta name="description" content="{meta_desc}">
    <link rel="canonical" href="{page_url}">

    <!-- Open Graph -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{seo_title}">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:image" content="{p1_img}">
    <meta property="og:url" content="{page_url}">
    <meta property="og:site_name" content="Radar de Preços">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{seo_title}">
    <meta name="twitter:description" content="{meta_desc}">
    <meta name="twitter:image" content="{p1_img}">

    <!-- Schema -->
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

        .site-header {{ background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); padding: 16px 20px; color: white; }}
        .site-header .inner {{ max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }}
        .site-header .logo {{ color: white; font-size: 20px; font-weight: 800; text-decoration: none; }}
        .site-header nav a {{ color: rgba(255,255,255,0.85); font-size: 14px; margin-left: 20px; }}

        .container {{ max-width: 1100px; margin: 0 auto; padding: 20px; }}
        .breadcrumb {{ font-size: 13px; color: #64748b; margin-bottom: 20px; }}
        .breadcrumb a {{ color: #1a73e8; }}
        .breadcrumb span {{ color: #94a3b8; margin: 0 6px; }}

        /* Hero */
        .comp-hero {{ text-align: center; padding: 30px 20px; background: white; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 28px; }}
        .comp-hero h1 {{ font-size: 26px; font-weight: 800; color: #0f172a; margin-bottom: 12px; line-height: 1.3; }}
        .comp-hero .vs-badge {{ display: inline-block; background: #1a73e8; color: white; padding: 4px 16px; border-radius: 20px; font-weight: 800; font-size: 18px; margin: 0 10px; }}
        .comp-hero p {{ color: #64748b; font-size: 15px; margin-top: 10px; }}

        /* Product Cards */
        .comp-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 28px; }}
        @media (max-width: 768px) {{ .comp-grid {{ grid-template-columns: 1fr; }} }}
        .product-card {{ background: white; padding: 25px; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; position: relative; transition: all 0.2s; }}
        .product-card.winner {{ border: 3px solid #ffd700; box-shadow: 0 4px 20px rgba(255,215,0,0.3); }}
        .winner-badge {{ position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #ffd700; color: #000; padding: 4px 16px; border-radius: 20px; font-size: 12px; font-weight: 800; white-space: nowrap; }}
        .product-card img {{ width: 160px; height: 160px; object-fit: contain; margin-bottom: 16px; border-radius: 8px; }}
        .product-card h2 {{ font-size: 15px; font-weight: 700; margin-bottom: 12px; line-height: 1.4; color: #0f172a; }}
        .product-card .price {{ font-size: 28px; font-weight: 800; color: #00c853; margin-bottom: 6px; }}
        .product-card .price-old {{ font-size: 13px; color: #94a3b8; text-decoration: line-through; margin-bottom: 8px; }}
        .product-card .discount {{ display: inline-block; background: #ff6b35; color: white; padding: 3px 10px; border-radius: 5px; font-size: 12px; font-weight: 700; margin-bottom: 16px; }}
        .btn-buy {{ display: block; padding: 14px; background: linear-gradient(135deg, #ff9800, #f57c00); color: white; border-radius: 8px; font-weight: 800; font-size: 15px; text-decoration: none; margin-top: 12px; transition: all 0.2s; }}
        .btn-buy:hover {{ transform: translateY(-2px); text-decoration: none; }}
        .btn-detail {{ display: block; padding: 10px; background: #f1f5f9; color: #1a73e8; border-radius: 8px; font-weight: 600; font-size: 13px; text-decoration: none; margin-top: 8px; }}

        /* Section */
        .section {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 24px; }}
        .section h2 {{ font-size: 20px; font-weight: 800; margin-bottom: 16px; color: #0f172a; padding-bottom: 10px; border-bottom: 2px solid #1a73e8; }}
        .section p {{ font-size: 15px; line-height: 1.75; color: #475569; }}

        /* Pros Grid */
        .pros-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 600px) {{ .pros-grid {{ grid-template-columns: 1fr; }} }}
        .pros-card {{ background: #f0fdf4; padding: 18px; border-radius: 10px; border-left: 4px solid #22c55e; }}
        .pros-card h3 {{ font-size: 14px; font-weight: 700; color: #166534; margin-bottom: 10px; }}
        .pros-card ul {{ list-style: none; padding: 0; }}
        .pros-card li {{ font-size: 13px; margin-bottom: 6px; line-height: 1.5; }}

        /* Recommendation */
        .rec-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media (max-width: 600px) {{ .rec-grid {{ grid-template-columns: 1fr; }} }}
        .rec-card {{ background: #f8fafc; padding: 18px; border-radius: 10px; border: 1px solid #e2e8f0; }}
        .rec-card h3 {{ font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }}
        .rec-card p {{ font-size: 13px; color: #475569; line-height: 1.6; }}

        /* Veredito */
        .veredito-box {{ background: linear-gradient(135deg, #fef9c3, #fef3c7); padding: 24px; border-radius: 12px; border-left: 5px solid #f59e0b; text-align: center; }}
        .veredito-box h2 {{ font-size: 22px; font-weight: 800; color: #92400e; margin-bottom: 10px; }}
        .veredito-box p {{ color: #78350f; font-size: 15px; }}

        /* FAQ */
        .faq-item {{ margin-bottom: 16px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
        .faq-q {{ background: #f8fafc; padding: 14px 18px; font-weight: 700; color: #1e293b; cursor: pointer; font-size: 14px; }}
        .faq-a {{ padding: 14px 18px; color: #475569; font-size: 14px; line-height: 1.7; }}

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
        <a href="{BASE_URL}/comparativos/">Comparativos</a>
        <span>›</span>
        <span style="color:#1e293b;">{p1_name[:30]} vs {p2_name[:30]}</span>
    </nav>

    <!-- Hero -->
    <div class="comp-hero">
        <h1>
            {p1_name[:50]}
            <span class="vs-badge">VS</span>
            {p2_name[:50]}
        </h1>
        <p>Comparativo completo com análise de preço, prós/contras e veredito do especialista • {NOW_BR}</p>
    </div>

    <!-- Product Cards -->
    <div class="comp-grid">
        <div class="product-card {'winner' if is_p1_winner else ''}">
            {'<span class="winner-badge">🏆 MELHOR ESCOLHA</span>' if is_p1_winner else ''}
            <img src="{p1_img}" alt="{p1_name}" loading="eager" width="160" height="160">
            <h2>{p1_name}</h2>
            <div class="price-old">De: {p1_orig}</div>
            <div class="price">{p1_price}</div>
            <span class="discount">{p1_discount}% OFF</span>
            <a href="{p1_url}" class="btn-buy" rel="nofollow noopener" target="_blank">
                🛒 Ver no Mercado Livre →
            </a>
            <a href="{p1_page}" class="btn-detail">Ver análise completa</a>
        </div>
        <div class="product-card {'winner' if not is_p1_winner else ''}">
            {'<span class="winner-badge">🏆 MELHOR ESCOLHA</span>' if not is_p1_winner else ''}
            <img src="{p2_img}" alt="{p2_name}" loading="eager" width="160" height="160">
            <h2>{p2_name}</h2>
            <div class="price-old">De: {p2_orig}</div>
            <div class="price">{p2_price}</div>
            <span class="discount">{p2_discount}% OFF</span>
            <a href="{p2_url}" class="btn-buy" rel="nofollow noopener" target="_blank">
                🛒 Ver no Mercado Livre →
            </a>
            <a href="{p2_page}" class="btn-detail">Ver análise completa</a>
        </div>
    </div>

    <!-- Resumo -->
    <div class="section">
        <h2>📊 Análise Comparativa</h2>
        <p>{analysis.get('resumo', '')}</p>
    </div>

    <!-- Veredito -->
    <div class="veredito-box" style="margin-bottom: 24px;">
        <h2>🏆 Veredito do Radar de Preços</h2>
        <p><strong>{analysis.get('vencedor', '')}</strong> é a melhor escolha: {analysis.get('motivo_vencedor', '')}</p>
    </div>

    <!-- Prós de cada produto -->
    <div class="section">
        <h2>✅ Pontos Fortes de Cada Um</h2>
        <div class="pros-grid">
            <div class="pros-card">
                <h3>👍 {p1_name[:40]}</h3>
                <ul>{p1_pros_html}</ul>
            </div>
            <div class="pros-card">
                <h3>👍 {p2_name[:40]}</h3>
                <ul>{p2_pros_html}</ul>
            </div>
        </div>
    </div>

    <!-- Recomendações -->
    <div class="section">
        <h2>🎯 Para Quem é Cada Um?</h2>
        <div class="rec-grid">
            <div class="rec-card">
                <h3>Escolha {p1_name[:35]} se...</h3>
                <p>{analysis.get('recomendacao_p1', '')}</p>
            </div>
            <div class="rec-card">
                <h3>Escolha {p2_name[:35]} se...</h3>
                <p>{analysis.get('recomendacao_p2', '')}</p>
            </div>
        </div>
    </div>

    <!-- Tabela de preços -->
    <div class="section">
        <h2>💰 Comparativo de Preços</h2>
        <table style="width:100%; border-collapse:collapse;">
            <thead>
                <tr style="background:#f8fafc;">
                    <th style="padding:12px 15px; text-align:left; border-bottom:2px solid #e2e8f0;">Produto</th>
                    <th style="padding:12px 15px; text-align:center; border-bottom:2px solid #e2e8f0;">Preço Atual</th>
                    <th style="padding:12px 15px; text-align:center; border-bottom:2px solid #e2e8f0;">Desconto</th>
                    <th style="padding:12px 15px; text-align:center; border-bottom:2px solid #e2e8f0;">Ação</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding:12px 15px; border-bottom:1px solid #e2e8f0; font-weight:600;">{p1_name[:45]}</td>
                    <td style="padding:12px 15px; border-bottom:1px solid #e2e8f0; text-align:center; color:#00c853; font-weight:800;">{p1_price}</td>
                    <td style="padding:12px 15px; border-bottom:1px solid #e2e8f0; text-align:center;"><span style="background:#ff6b35;color:white;padding:3px 8px;border-radius:4px;font-size:12px;font-weight:700;">{p1_discount}% OFF</span></td>
                    <td style="padding:12px 15px; border-bottom:1px solid #e2e8f0; text-align:center;"><a href="{p1_url}" rel="nofollow noopener" target="_blank" style="background:#1a73e8;color:white;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;">Ver Oferta</a></td>
                </tr>
                <tr style="background:#f8fafc;">
                    <td style="padding:12px 15px; font-weight:600;">{p2_name[:45]}</td>
                    <td style="padding:12px 15px; text-align:center; color:#00c853; font-weight:800;">{p2_price}</td>
                    <td style="padding:12px 15px; text-align:center;"><span style="background:#ff6b35;color:white;padding:3px 8px;border-radius:4px;font-size:12px;font-weight:700;">{p2_discount}% OFF</span></td>
                    <td style="padding:12px 15px; text-align:center;"><a href="{p2_url}" rel="nofollow noopener" target="_blank" style="background:#1a73e8;color:white;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;">Ver Oferta</a></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- FAQ -->
    <div class="section">
        <h2>❓ Perguntas Frequentes</h2>
        {faq_html}
    </div>

    <!-- Navegação -->
    <div style="text-align:center; margin:30px 0; padding-top:20px; border-top:1px solid #e2e8f0;">
        <a href="{BASE_URL}/comparativos/" style="color:#1a73e8; font-weight:600; margin-right:20px;">
            ← Ver Todos os Comparativos
        </a>
        <a href="{BASE_URL}/categorias/{category}/" style="color:#1a73e8; font-weight:600;">
            Ver Mais em {CATEGORY_NAMES.get(category, category)} →
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
        Somos afiliados do Mercado Livre. Ganhamos comissão por vendas realizadas através dos nossos links.
    </p>
</footer>

</body>
</html>"""

    filename = f"comparativos/{comp_slug}.html"
    return html, filename


def main():
    print("=" * 60)
    print("🥊 GERADOR NINJA DE COMPARATIVOS")
    print(f"   Data: {NOW_BR}")
    print("=" * 60)

    # Carregar produtos
    products_file = ROOT / "data" / "database" / "validated_200_products.json"
    with open(products_file, encoding="utf-8") as f:
        all_products = json.load(f)

    print(f"\n📦 {len(all_products)} produtos disponíveis")

    # Criar diretório de comparativos
    comp_dir = ROOT / "comparativos"
    comp_dir.mkdir(exist_ok=True)

    success = 0
    errors = 0
    generated = []

    for i, (name1, name2) in enumerate(HIGH_INTENT_PAIRS, 1):
        print(f"\n[{i:02d}/{len(HIGH_INTENT_PAIRS)}] {name1[:35]} vs {name2[:35]}")

        p1 = find_product(all_products, name1)
        p2 = find_product(all_products, name2)

        if not p1:
            print(f"  ⚠️  Produto 1 não encontrado: {name1[:40]}")
            errors += 1
            continue
        if not p2:
            print(f"  ⚠️  Produto 2 não encontrado: {name2[:40]}")
            errors += 1
            continue

        print(f"  ✓ P1: {p1.get('name', '')[:50]}")
        print(f"  ✓ P2: {p2.get('name', '')[:50]}")

        try:
            html, filename = generate_comparison_page(p1, p2)
            output_path = ROOT / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            generated.append(filename)
            success += 1
            print(f"  ✅ Salvo: {filename}")

        except Exception as e:
            errors += 1
            print(f"  ❌ Erro: {e}")

    # Gerar índice de comparativos
    print(f"\n📋 Gerando índice de comparativos...")
    generate_comparativos_index(generated, all_products)

    print("\n" + "=" * 60)
    print(f"✅ CONCLUÍDO: {success} comparativos gerados, {errors} erros")
    print("=" * 60)


def generate_comparativos_index(comp_files: list, all_products: list):
    """Gera página de índice dos comparativos."""
    cards_html = ""
    for f in comp_files:
        fname = os.path.basename(f)
        # Extrair nomes do slug
        parts = fname.replace(".html", "").split("-vs-")
        if len(parts) == 2:
            name1 = parts[0].replace("-", " ").title()[:40]
            name2 = parts[1].replace("-", " ").title()[:40]
            cards_html += f"""
            <a href="{BASE_URL}/comparativos/{fname}" class="comp-card">
                <div class="vs-label">VS</div>
                <div class="comp-names">
                    <span>{name1}</span>
                    <strong>vs</strong>
                    <span>{name2}</span>
                </div>
                <div class="comp-cta">Ver Comparativo →</div>
            </a>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparativos de Produtos — Qual o Melhor? | Radar de Preços</title>
    <meta name="description" content="Compare produtos lado a lado. Análise detalhada de prós, contras e custo-benefício. Encontre o melhor produto para você.">
    <link rel="canonical" href="{BASE_URL}/comparativos/">
    <meta name="google-adsense-account" content="ca-pub-4896859041377751">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Inter',sans-serif; background:#f5f7fa; color:#1e293b; }}
        .site-header {{ background:linear-gradient(135deg,#1a73e8,#0d47a1); padding:16px 20px; color:white; }}
        .site-header .inner {{ max-width:1100px; margin:0 auto; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; }}
        .site-header .logo {{ color:white; font-size:20px; font-weight:800; text-decoration:none; }}
        .site-header nav a {{ color:rgba(255,255,255,0.85); font-size:14px; margin-left:20px; text-decoration:none; }}
        .container {{ max-width:1100px; margin:0 auto; padding:30px 20px; }}
        .page-title {{ text-align:center; margin-bottom:40px; }}
        .page-title h1 {{ font-size:32px; font-weight:800; color:#0f172a; margin-bottom:12px; }}
        .page-title p {{ color:#64748b; font-size:16px; }}
        .comp-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px; }}
        .comp-card {{ background:white; padding:20px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.08); text-decoration:none; color:#1e293b; transition:all 0.2s; display:block; }}
        .comp-card:hover {{ transform:translateY(-3px); box-shadow:0 6px 16px rgba(0,0,0,0.12); text-decoration:none; }}
        .vs-label {{ display:inline-block; background:#1a73e8; color:white; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:800; margin-bottom:12px; }}
        .comp-names {{ display:flex; flex-direction:column; gap:4px; margin-bottom:14px; }}
        .comp-names span {{ font-size:14px; font-weight:600; color:#0f172a; }}
        .comp-names strong {{ font-size:12px; color:#94a3b8; }}
        .comp-cta {{ font-size:13px; color:#1a73e8; font-weight:600; }}
        footer {{ background:#0f172a; color:#94a3b8; padding:30px 20px; text-align:center; margin-top:40px; }}
        footer p {{ font-size:13px; margin-bottom:6px; }}
        footer a {{ color:#64748b; }}
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
    <div class="page-title">
        <h1>🥊 Comparativos de Produtos</h1>
        <p>Compare produtos lado a lado e descubra qual oferece o melhor custo-benefício para você.</p>
    </div>
    <div class="comp-grid">
        {cards_html}
    </div>
</main>
<footer>
    <p>© 2026 Radar de Preços — As melhores ofertas do Mercado Livre.</p>
    <p><a href="{BASE_URL}/privacidade/">Privacidade</a> · <a href="{BASE_URL}/termos/">Termos</a> · <a href="{BASE_URL}/sobre/">Sobre</a></p>
</footer>
</body>
</html>"""

    index_path = ROOT / "comparativos" / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Índice salvo: comparativos/index.html")


if __name__ == "__main__":
    main()
