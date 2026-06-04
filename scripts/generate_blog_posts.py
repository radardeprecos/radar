import html
import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
    AI_ENABLED = True
except Exception:
    AI_ENABLED = False

from logger import logger

BASE_URL = "https://radardeprecos.github.io/"
ROOT = Path(__file__).resolve().parents[1]

# Configuração Portal Único
POSTS_DIR = ROOT / "noticias" / "posts"
NEWS_INDEX = ROOT / "noticias" / "index.html"
PRODUCTS_FILE = ROOT / "data" / "database" / "all_products.json"

def slugify(text: str, max_len: int = 90) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:max_len].strip("-") or "oferta"

def money(value: Any) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Preço indisponível"

def load_products() -> List[Dict[str, Any]]:
    if not PRODUCTS_FILE.exists():
        logger.error(f"Banco de dados de produtos não encontrado: {PRODUCTS_FILE}")
        return []
    with PRODUCTS_FILE.open("r", encoding="utf-8") as f:
        products = json.load(f)
    active = [p for p in products if p.get("status", "active") == "active" and p.get("name")]
    active.sort(key=lambda p: float(p.get("custom_discount_pct") or 0), reverse=True)
    return active

def get_already_published_ids() -> set:
    if not NEWS_INDEX.exists():
        return set()
    content = NEWS_INDEX.read_text(encoding="utf-8")
    ids = set(re.findall(r'MLB[0-9]+', content))
    return ids

def select_products(products: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    published_ids = get_already_published_ids()
    available = [p for p in products if str(p.get("id")) not in published_ids]
    
    if not available:
        logger.warning("Todos os produtos do banco já possuem artigos publicados.")
        return []
        
    return available[:count]

def generate_long_content(product: Dict[str, Any]) -> str:
    name = product.get("name", "Produto")
    discount = product.get("custom_discount_pct", 0)
    price = money(product.get("price"))
    
    return f"""
    <p>O <strong>{html.escape(name)}</strong> está sendo monitorado pelo Radar Ninja e acaba de atingir um nível de preço digno de alerta. Com <strong>{discount}% de desconto</strong>, esta é uma das melhores oportunidades do dia.</p>
    <h2>Por que vale a pena?</h2>
    <p>O preço de {price} está abaixo da média histórica para este modelo. Nossa análise automática indica que este valor é real e não uma "maquiagem" de preços pré-evento.</p>
    <h2>Pontos de Atenção</h2>
    <ul>
        <li>Verifique o valor do frete para sua região, pois pode impactar o custo-benefício.</li>
        <li>O estoque de ofertas agressivas costuma durar poucos minutos.</li>
    </ul>
    """

def render_post(product: Dict[str, Any], now: datetime, sequence: int) -> tuple:
    safe_name = product.get("name", "produto")
    p_id = product.get("id", "0")
    title = f"Alerta de Oferta: {safe_name} vale a pena com {product.get('custom_discount_pct', 0)}% OFF?"
    slug = f"analise-{slugify(safe_name)}-{p_id}-{now.strftime('%Y%m%d%H%M%S')}-{sequence}"
    
    canonical = f"{BASE_URL}noticias/posts/{slug}.html"
    article_body = generate_long_content(product)
    image = html.escape(product.get("image") or product.get("thumbnail") or "")
    offer_url = html.escape(product.get("custom_affiliate_url") or product.get("permalink") or "#")
    
    content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} | Radar de Preços</title>
    <meta name="description" content="Alerta de Oferta automática do Radar de Preços sobre {html.escape(safe_name)}, preço, desconto e pontos de atenção antes de comprar.">
    <link rel="canonical" href="{canonical}">
    <link rel="stylesheet" href="../../assets/css/style.css">
</head>
<body>
    <header class="header"><div class="container"><a href="../../" class="logo">📊 Radar de Preços</a></div></header>
    <main class="container" style="padding: 40px 20px; max-width: 860px; margin: 0 auto;">
        <article>
            <header style="margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 20px;">
                <div style="color: var(--primary); font-weight: bold; margin-bottom: 10px;">ANÁLISE AUTOMÁTICA DO RADAR NINJA</div>
                <h1>{html.escape(title)}</h1>
                <p style="color: #666;">Equipe Radar de Preços | {now.strftime('%d/%m/%Y %H:%M')}</p>
            </header>
            <section style="background: #f9f9f9; padding: 20px; border-radius: 12px; display: flex; gap: 20px; align-items: center; margin-bottom: 30px; flex-wrap: wrap;">
                <img src="{image}" alt="{html.escape(safe_name)}" style="width: 160px; height: 160px; object-fit: contain; background: white; border-radius: 8px;">
                <div>
                    <div style="font-size: 26px; font-weight: 800; color: #d32f2f;">{money(product.get('price'))}</div>
                    <div style="color: #388e3c; font-weight: bold;">{product.get('custom_discount_pct', 0)}% OFF monitorado</div>
                    <a href="{offer_url}" class="btn" style="margin-top: 15px; display: inline-block;">Ver Oferta no Mercado Livre</a>
                </div>
            </section>
            <div class="content">{article_body}</div>
            <footer style="margin-top: 40px; text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
                <a href="../../noticias/" style="color: var(--primary); text-decoration: none; font-weight: bold;">← Ver todas as notícias</a>
            </footer>
        </article>
    </main>
</body>
</html>
"""
    return title, slug, content

def update_news_index(title: str, slug: str, product: Dict[str, Any], now: datetime) -> None:
    if not NEWS_INDEX.exists():
        logger.warning(f"Índice de notícias não encontrado: {NEWS_INDEX}")
        return
    content = NEWS_INDEX.read_text(encoding="utf-8")
    url = f"posts/{slug}.html"
    
    entry = {
        "id": int(now.timestamp()),
        "tag": "analise",
        "tagLabel": "📊 Alerta de Oferta",
        "tagClass": "tag-analise",
        "icon": "🔍",
        "title": title,
        "excerpt": f"Alerta de Oferta automática do Radar de Preços sobre {product.get('name', 'produto')[:80]} com {product.get('custom_discount_pct', 0)}% de desconto monitorado.",
        "date": now.strftime("%d %b %Y"),
        "readTime": "5 min",
        "featured": True,
        "url": url,
    }
    
    serialized = json.dumps(entry, ensure_ascii=False, indent=8)
    marker = "const NEWS = ["
    if marker not in content:
        logger.warning("Marcador const NEWS = [ não encontrado; índice não atualizado.")
        return
        
    content = content.replace(marker, f"{marker}\n        {serialized},", 1)
    NEWS_INDEX.write_text(content, encoding="utf-8")

def generate_blog_content(count: int = 1) -> List[Path]:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    products = load_products()
    selected = select_products(products, count)
    
    if not selected:
        logger.info("Nenhum produto novo disponível para gerar artigos.")
        return []
        
    created: List[Path] = []
    now = datetime.now()
    for sequence, product in enumerate(selected, start=1):
        title, slug, content = render_post(product, now, sequence)
        file_path = POSTS_DIR / f"{slug}.html"
        file_path.write_text(content, encoding="utf-8")
        update_news_index(title, slug, product, now)
        created.append(file_path)
        logger.info(f"Artigo gerado: {file_path.relative_to(ROOT)}")
        
    logger.info(f"Total de artigos gerados nesta execução: {len(created)}")
    return created

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("BLOG_POST_COUNT", "1"))
    generate_blog_content(max(1, count))
