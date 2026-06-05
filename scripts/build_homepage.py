import os
import json
import re
import unicodedata
from datetime import datetime, timedelta
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
    logger.info(f"Construindo página inicial com lógica de rotação e SELOS PREMIUM...")
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
        
        # Usar link de afiliado direto na home para evitar cliques extras
        p_url = p.get('custom_affiliate_url') or p.get('permalink', '')
        
        p_img = p.get("image") or p.get("thumbnail") or ""
        p_price = money(p.get("price"))
        p_old = money(p.get("originalPrice") or p.get("original_price"))
        p_disc = p.get("custom_discount_pct", 0)
        
        badge_ninja = ""
        if p_disc >= 40:
            badge_ninja = '<span style="position: absolute; top: 10px; left: 10px; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); color: white; padding: 4px 10px; border-radius: 6px; font-weight: 900; font-size: 10px; z-index: 20; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">🔥 OFERTA NINJA</span>'

        products_html += f"""
        <div class="product-card" style="position: relative; background: white; border-radius: 12px; overflow: hidden; border: 1px solid #E2E8F0; display: flex; flex-direction: column; transition: transform 0.3s ease;">
            {badge_ninja}
            <span style="position: absolute; top: 10px; right: 10px; background: #EF4444; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 12px; z-index: 10;">↓ {p_disc}% OFF</span>
            <div style="aspect-ratio: 1/1; padding: 20px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #F1F5F9;">
                <img src="{p_img}" alt="{p_name}" style="max-width: 100%; max-height: 100%; object-fit: contain;" loading="lazy">
            </div>
            <div style="padding: 15px; flex-grow: 1; display: flex; flex-direction: column;">
                <h3 style="font-size: 14px; font-weight: 700; color: #0F172A; margin-bottom: 10px; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{p_name}</h3>
                <div style="margin-bottom: 10px;">
                    <span style="font-size: 12px; color: #94A3B8; text-decoration: line-through;">{p_old}</span>
                    <span style="font-size: 18px; font-weight: 900; color: #1E3A8A; display: block;">{p_price}</span>
                </div>
                <div style="margin-bottom: 15px; display: flex; align-items: center; gap: 5px; font-size: 10px; color: #10B981; font-weight: 700;">
                    <span>✅ Preço Verificado</span>
                </div>
                <a href="{p_url}" target="_blank" style="background: #F59E0B; color: #78350F; text-align: center; text-decoration: none; padding: 10px; border-radius: 8px; font-weight: 800; font-size: 14px; margin-top: auto; transition: background 0.2s;">🛒 Ir para a Loja</a>
            </div>
        </div>
        """

    # Manter compatibilidade com o template original
    content = template.replace("{{products_html}}", products_html)
    # Se o template usar outro marcador:
    content = content.replace("{{products_grid}}", products_html)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Homepage gerada com {len(display_products)} produtos e SELOS PREMIUM.")

if __name__ == "__main__":
    build_homepage(
        "data/database/all_products.json", 
        "noticias/index.html", 
        "templates/homepage.html", 
        "index.html",
        "data/history/homepage_rotation.json"
    )
