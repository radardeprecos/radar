import json
import os
from datetime import datetime
from logger import logger

def generate_ranking_post(category, products):
    # Filtrar por categoria e ordenar por desconto
    cat_products = [p for p in products if p.get('category') == category]
    cat_products.sort(key=lambda x: x.get('custom_discount_pct', 0), reverse=True)
    top_5 = cat_products[:5]
    
    if not top_5: return

    now = datetime.now()
    file_name = f"top-5-{category.lower()}-{now.strftime('%Y-%m-%d')}.html"
    file_path = f"noticias/posts/{file_name}"
    
    content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Top 5 Melhores Ofertas de {category} - {now.strftime('%d/%m/%Y')}</title>
        <link rel="stylesheet" href="../../assets/css/style.css">
    </head>
    <body>
        <header class="header"><div class="container"><a href="../../" class="logo">📊 Radar de Preços</a></div></header>
        <main class="container" style="max-width: 800px; margin: 40px auto; padding: 0 20px;">
            <h1>🏆 Top 5 Melhores Ofertas: {category}</h1>
            <p style="color:#64748b">Atualizado em {now.strftime('%d/%m/%Y %H:%M')}</p>
            <div style="margin-top:30px;">
    """
    
    for i, p in enumerate(top_5):
        content += f"""
        <div style="display:flex; gap:20px; background:white; padding:20px; border-radius:12px; border:1px solid #e2e8f0; margin-bottom:20px; align-items:center;">
            <div style="font-size:24px; font-weight:800; color:#14b8a6;">#{i+1}</div>
            <img src="{p.get('image')}" style="width:80px; height:80px; object-fit:contain;">
            <div style="flex:1">
                <h3 style="font-size:16px; margin:0;">{p.get('name')}</h3>
                <div style="color:#16a34a; font-weight:bold; margin-top:5px;">R$ {p.get('price')} (-{p.get('custom_discount_pct')}% OFF)</div>
            </div>
            <a href="{p.get('permalink')}" style="background:#14b8a6; color:white; padding:10px 15px; border-radius:6px; text-decoration:none; font-weight:bold; font-size:12px;">VER OFERTA</a>
        </div>
        """
        
    content += """
            </div>
            <div style="margin-top:40px; padding:30px; background:#f0fdf4; border:2px dashed #16a34a; border-radius:12px; text-align:center;">
                <h3>🚀 Quer receber essas ofertas primeiro?</h3>
                <p>Entre no nosso Grupo VIP e não perca nenhum erro de preço!</p>
                <a href="/radar/vip/" style="display:inline-block; margin-top:15px; background:#16a34a; color:white; padding:15px 30px; border-radius:8px; text-decoration:none; font-weight:bold;">QUERO ENTRAR NO GRUPO VIP</a>
            </div>
        </main>
    </body>
    </html>
    """
    
    os.makedirs("noticias/posts", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Ranking gerado: {file_path}")

def build_all():
    db_path = "data/database/all_products.json"
    if not os.path.exists(db_path): return
    with open(db_path, "r") as f:
        products = json.load(f)
    
    categories = list(set([p.get('category') for p in products if p.get('category')]))
    for cat in categories:
        generate_ranking_post(cat, products)

if __name__ == "__main__":
    build_all()
