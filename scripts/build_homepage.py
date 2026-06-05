import os
import json
import re
import unicodedata
from datetime import datetime, timedelta
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

def load_rotation_history(history_path):
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_rotation_history(history_path, history):
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def build_homepage(input_path, news_index_path, template_path, output_path, history_path):
    logger.info(f"Construindo página inicial com lógica de rotação e DESIGN NINJA...")
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
    
    history = load_rotation_history(history_path)
    now = datetime.now()
    threshold = now - timedelta(hours=48)
    
    available_products = []
    recent_ids = set()
    for pid, date_str in history.items():
        try:
            if datetime.fromisoformat(date_str) > threshold:
                recent_ids.add(pid)
        except:
            pass
    
    for p in active_products:
        p_id = str(p.get("id"))
        if p_id not in recent_ids:
            available_products.append(p)
    
    if len(available_products) < 12:
        available_products = active_products
    
    available_products.sort(key=lambda x: x.get("custom_discount_pct", 0), reverse=True)
    display_products = available_products[:24]
    
    for p in display_products:
        history[str(p.get("id"))] = now.isoformat()
    save_rotation_history(history_path, history)

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
        
        try:
            savings_val = float(p.get("originalPrice") or p.get("original_price") or 0) - float(p.get("price", 0))
            savings_text = money(savings_val)
        except:
            savings_text = "R$ 0,00"

        is_hot = p_disc > 50

        disc_bar_width = min(int(p_disc), 100)
        products_html += f"""
        <div class="product-card">
            <div class="card-badges">
                <span class="badge-best-price">⭐ Oferta</span>
                {f'<span class="badge-hot">🔥 Destaque</span>' if is_hot else ''}
            </div>
            <div class="product-img-wrapper">
                <img src="{p_img}" alt="{p_name}" class="product-image" loading="lazy" width="200" height="200">
            </div>
            <h3 class="product-title">{p_name}</h3>
            <div class="price-container">
                <span class="price-old">De {p_old}</span>
                <span class="price-current">{p_price}</span>
            </div>
            <div class="savings-badge">💰 Economize {savings_text}</div>
            <div class="discount-bar-wrap">
                <div class="discount-bar"><div class="discount-bar-fill" style="width:{disc_bar_width}%"></div></div>
            </div>
            <a href="{p_url}" class="btn-ninja">🛒 Ver Oferta</a>
        </div>
        """

    if 'ninja-style.css' not in template:
        template = template.replace('</head>', '    <link rel="stylesheet" href="/assets/css/ninja-style.css">\n</head>')

    content = template.replace("{{products_html}}", products_html)
    content = content.replace('style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 25px; margin-top: 30px;"', 'class="products-grid" id="products-grid"')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Homepage gerada com {len(display_products)} produtos e DESIGN NINJA.")

if __name__ == "__main__":
    build_homepage(
        "data/database/all_products.json", 
        "noticias/index.html", 
        "templates/homepage.html", 
        "index.html",
        "data/history/homepage_rotation.json"
    )
