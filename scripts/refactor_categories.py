import os
import re
from bs4 import BeautifulSoup

base_dir = '/home/ubuntu/radardeprecos.github.io/radar'
ofertas_dir = os.path.join(base_dir, 'ofertas')

# Template visual premium para categorias
template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ofertas de {category_name} — Radar Ninja</title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap">
    <style>
        :root {{
            --primary: #00c853;
            --primary-dark: #00a443;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #0f172a;
            --border: #e2e8f0;
            --shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
        .header {{ background: #0f172a; padding: 15px 0; }}
        .hero-mini {{ background: #1e293b; color: white; padding: 40px 0; text-align: center; border-bottom: 4px solid var(--primary); }}
        .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 25px; margin: 40px 0; }}
        .product-card {{ background: var(--card); border-radius: 16px; border: 1px solid var(--border); overflow: hidden; transition: 0.3s; display: flex; flex-direction: column; }}
        .product-card:hover {{ transform: translateY(-5px); box-shadow: var(--shadow); }}
        .card-img {{ height: 200px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
        .card-img img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .card-body {{ padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }}
        .card-title {{ font-weight: 700; font-size: 1rem; margin-bottom: 10px; line-height: 1.4; }}
        .card-price {{ font-size: 1.25rem; font-weight: 800; color: var(--primary); margin-top: auto; }}
        .btn-ninja {{ background: var(--primary); color: white; padding: 10px; border-radius: 8px; text-decoration: none; text-align: center; font-weight: 700; margin-top: 15px; }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container" style="display: flex; justify-content: space-between; align-items: center;">
            <a href="/" style="font-size: 1.5rem; font-weight: 900; color: white; text-decoration: none;">🥷 RADAR NINJA</a>
            <nav style="display: flex; gap: 20px;">
                <a href="/ofertas-hoje/" style="color: white; text-decoration: none; font-weight: 600;">Ofertas</a>
                <a href="/noticias/" style="color: white; text-decoration: none; font-weight: 600;">Notícias</a>
            </nav>
        </div>
    </header>

    <section class="hero-mini">
        <div class="container">
            <h1>Ofertas de {category_name}</h1>
            <p>Os melhores preços encontrados pela nossa IA em {category_name}</p>
        </div>
    </section>

    <main class="container">
        <div class="products-grid">
            {product_cards}
        </div>
    </main>

    <footer style="background: #0f172a; color: white; padding: 40px 0; margin-top: 60px; text-align: center;">
        <div class="container">
            <p>&copy; 2026 Radar Ninja</p>
        </div>
    </footer>
</body>
</html>"""

def extract_product_info(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        title = soup.find('h1').text if soup.find('h1') else "Produto"
        if len(title) > 60: title = title[:57] + "..."
        
        price = soup.find(class_='price-tag').text.split(' ')[0] if soup.find(class_='price-tag') else "Ver preço"
        
        img_tag = soup.find('img', alt=True)
        img_src = img_tag['src'] if img_tag else "/assets/img/placeholder.png"
        
        return {
            'title': title,
            'price': price,
            'img': img_src,
            'url': os.path.basename(file_path)
        }
    except:
        return None

categories = [d for d in os.listdir(ofertas_dir) if os.path.isdir(os.path.join(ofertas_dir, d))]

for cat in categories:
    cat_path = os.path.join(ofertas_dir, cat)
    products = [f for f in os.listdir(cat_path) if f.endswith('.html') and f != 'index.html']
    
    cards_html = ""
    for p in products:
        info = extract_product_info(os.path.join(cat_path, p))
        if info:
            cards_html += f"""
            <div class="product-card">
                <div class="card-img"><img src="{info['img']}" alt="{info['title']}"></div>
                <div class="card-body">
                    <div class="card-title">{info['title']}</div>
                    <div class="card-price">{info['price']}</div>
                    <a href="{info['url']}" class="btn-ninja">Ver Oferta</a>
                </div>
            </div>"""
    
    if not cards_html:
        cards_html = "<p>Nenhuma oferta ativa no momento.</p>"
        
    final_html = template.format(category_name=cat.capitalize(), product_cards=cards_html)
    
    with open(os.path.join(cat_path, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Refatorado index.html para {cat}")
