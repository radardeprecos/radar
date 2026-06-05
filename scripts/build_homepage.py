import os
import json
import re
import unicodedata
from datetime import datetime, timedelta
from logger import logger

def money(value):
    try:
        return 'R$ ' + f"{float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "N/A"

def escHtml(str_val):
    return str(str_val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def build_homepage(input_path, template_path, output_path):
    logger.info(f"🚀 Blindagem Ativa: Gerando home com visual Super Robô...")
    
    if not os.path.exists(template_path):
        logger.error(f"Template {template_path} não encontrado!")
        return

    # Carregar produtos (usando o offers.json final)
    products = []
    if os.path.exists(input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            products = json.load(f)
    
    # Pegar as top 24 ofertas por desconto
    products.sort(key=lambda x: x.get("custom_discount_pct", 0), reverse=True)
    display_products = products[:48] # Aumentamos para 48 para dar volume
    
    products_html = ""
    for p in display_products:
        pct = p.get("custom_discount_pct", 0)
        p_id = p.get("id", "")
        p_name = p.get("title") or p.get("name") or "Produto"
        p_url = p.get("custom_affiliate_url") or p.get("permalink", "#")
        p_img = p.get("image") or p.get("thumbnail") or ""
        p_price = p.get("price", 0)
        p_old = p.get("original_price") or p.get("originalPrice")
        
        # Gerar o HTML do Card compatível com o CSS do Super Robô
        badge_class = "badge-fire" if pct >= 60 else ("badge-ninja" if pct >= 40 else ("badge-good" if pct >= 20 else "badge-ok"))
        badge_text = "🔥 OFERTA NINJA" if pct >= 60 else ("⚡ MEGA OFERTA" if pct >= 40 else ("✅ BOA OFERTA" if pct >= 20 else "💡 OFERTA"))
        
        # Simular sparkline estático no HTML (o JS do Super Robô vai animar se necessário, mas deixamos a estrutura)
        sparkline = '<div class="price-sparkline">' + ''.join(['<div class="bar" style="height:'+str(20+i*10)+'%"></div>' for i in range(7)]) + '</div>'

        products_html += f"""
    <div class="card" onclick="openModal('{p_id}')">
      <div class="card-badge {badge_class}">{badge_text}</div>
      <div class="card-img-wrap">
        <img src="{p_img}" alt="{escHtml(p_name)}" loading="lazy" onerror="this.src='data:image/svg+xml,<svg xmlns=\\'http://www.w3.org/2000/svg\\' viewBox=\\'0 0 100 100\\'><text y=\\'.9em\\' font-size=\\'80\\'>📦</text></svg>'">
      </div>
      <div class="card-body">
        <h3>{escHtml(p_name)}</h3>
        <div class="price-row">
          {f'<span class="old-price">{money(p_old)}</span>' if p_old else ''}
          <span class="new-price">{money(p_price)}</span>
          {f'<span class="discount-tag">-{pct}%</span>' if pct > 0 else ''}
        </div>
        <div class="discount-bar"><div class="discount-bar-fill" style="width:{min(pct, 100)}%"></div></div>
        {sparkline}
        <div class="card-meta">
          <span>📦 {p.get("custom_category_slug", "outros")}</span>
          <span class="verified">✔ Verificado</span>
        </div>
        <div class="card-actions">
          <a class="btn-primary" href="{p_url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">🛒 Ver Oferta</a>
          <button class="btn-fav" onclick="toggleFav('{p_id}', event)" title="Favoritar">♥</button>
        </div>
      </div>
    </div>"""

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Injetar o HTML gerado no template
    final_content = template.replace("{{products_grid}}", products_html)
    
    # Atualizar estatísticas no HTML (opcional, mas bom para o visual)
    total_val = len(products)
    avg_disc = int(sum(p.get("custom_discount_pct", 0) for p in products)/total_val) if total_val > 0 else 0
    
    final_content = final_content.replace('<div class="num" id="totalOffers">0</div>', f'<div class="num" id="totalOffers">{total_val}</div>')
    final_content = final_content.replace('<div class="num" id="avgDiscount">0%</div>', f'<div class="num" id="avgDiscount">{avg_disc}%</div>')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    logger.info(f"✅ Homepage blindada e atualizada com {len(display_products)} produtos.")

if __name__ == "__main__":
    build_homepage(
        "data/products/offers.json", 
        "templates/super_robot_template.html", 
        "index.html"
    )
