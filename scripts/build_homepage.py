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

def extract_news_from_index(news_index_path):
    if not os.path.exists(news_index_path):
        return []
    with open(news_index_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    match = re.search(r'const NEWS = \[(.*?)\];', content, re.DOTALL)
    if not match:
        return []
    
    news_json_str = "[" + match.group(1) + "]"
    news_json_str = re.sub(r',\s*\]', ']', news_json_str)
    
    try:
        news_data = json.loads(news_json_str)
        return news_data
    except Exception as e:
        logger.error(f"Erro ao parsear NEWS do index: {e}")
        return []

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
    logger.info(f"Construindo página inicial com lógica de rotação...")
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
        logger.warning(f"Poucos produtos inéditos ({len(available_products)}). Relaxando regra de rotação.")
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
        
        products_html += f"""
        <div class="product-card">
            <div class="badge-discount">{p_disc}% OFF</div>
            <img src="{p_img}" alt="{p_name}" class="product-image">
            <h3 class="product-title">{p_name}</h3>
            <div class="price-container">
                <span class="price-current">{p_price}</span>
                <span class="price-old">{p_old}</span>
            </div>
            <a href="{p_url}" class="btn">VER ALERTA</a>
        </div>
        """

    news_list = extract_news_from_index(news_index_path)
    news_html = ""
    if news_list:
        for item in news_list[:3]:
            n_title = item.get("title", "Análise Radar")
            n_excerpt = item.get("excerpt", "Confira os detalhes desta oferta monitorada.")
            n_url = f"noticias/{item.get('url')}"
            n_date = item.get("date", "")
            news_html += f"""
            <div style="background: white; padding: 25px; border-radius: 16px; border: 1px solid #eee; transition: transform 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                <div style="color: #667eea; font-size: 12px; font-weight: 800; margin-bottom: 10px; text-transform: uppercase;">📊 Alerta de Oferta • {n_date}</div>
                <h3 style="font-size: 18px; font-weight: 800; margin-bottom: 12px; line-height: 1.4; color: #333;">{n_title}</h3>
                <p style="font-size: 14px; color: #666; line-height: 1.6; margin-bottom: 20px;">{n_excerpt[:120]}...</p>
                <a href="{n_url}" style="color: #667eea; text-decoration: none; font-weight: 700; font-size: 14px; display: flex; align-items: center; gap: 5px;">
                    Ler Análise Completa <span>→</span>
                </a>
            </div>
            """
    else:
        news_html = "<p style='grid-column: 1/-1; text-align: center; color: #666;'>Nenhuma notícia recente disponível.</p>"

    content = template.replace("{{products_html}}", products_html)
    if "{{news_html}}" in content:
        content = content.replace("{{news_html}}", news_html)
    else:
        news_section = f"""
    <section class="blog-highlights" style="background: #f8f9fa; padding: 80px 0; border-top: 1px solid #eee;">
        <div class="container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
                <div>
                    <h2 style="font-size: 32px; font-weight: 900; margin-bottom: 10px;">📰 Radar de Notícias</h2>
                    <p style="color: #666;">Análises profundas geradas por nossa IA sobre as melhores oportunidades.</p>
                </div>
                <a href="/radar/noticias" class="btn" style="width: auto; padding: 12px 30px; background: white; color: #667eea; border: 2px solid #667eea;">Ver Tudo</a>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px;">
                {news_html}
            </div>
        </div>
    </section>
        """
        content = content.replace('<footer class="footer">', f"{news_section}\n    <footer class=\"footer\">")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Homepage gerada com {len(display_products)} produtos (rotação ativa) e {len(news_list[:3])} notícias.")

if __name__ == "__main__":
    build_homepage(
        "data/database/all_products.json", 
        "noticias/index.html", 
        "templates/homepage.html", 
        "index.html",
        "data/history/homepage_rotation.json"
    )
