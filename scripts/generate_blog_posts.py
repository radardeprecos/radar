import json
import os
import random
from datetime import datetime

def generate_blog_content():
    posts_dir = 'noticias/posts'
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)

    now = datetime.now()
    # Gera um título e slug baseados na data/hora para garantir que o robô publique algo novo
    post_title = f"Radar de Ofertas: Destaques de {now.strftime('%d de %B de %Y')}"
    post_slug = f"radar-ofertas-{now.strftime('%Y-%m-%d-%H-%M-%S')}"
    
    # Tenta pegar algumas ofertas reais para o post
    offers_file = 'data/products/offers.json'
    offers_summary = "<p>Hoje nosso robô identificou diversas oportunidades com descontos reais acima de 30%.</p>"
    
    if os.path.exists(offers_file):
        try:
            with open(offers_file, 'r') as f:
                products = json.load(f)
                # Seleciona 3 produtos aleatórios com desconto > 30% para variar o conteúdo
                eligible_products = [p for p in products if p.get('custom_discount_pct', 0) > 30]
                if len(eligible_products) >= 3:
                    top_3 = random.sample(eligible_products, 3)
                else:
                    top_3 = eligible_products
                offers_summary += "<ul>"
                for p in top_3:
                    offers_summary += f"<li><strong>{p.get('name', p.get('title'))}</strong>: {p.get('custom_discount_pct')}% de desconto!</li>"
                offers_summary += "</ul>"
        except:
            pass

    content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{post_title} | Radar de Preços</title>
        <link rel="stylesheet" href="../../assets/css/style.css">
    </head>
    <body>
        <header class="header"><div class="container"><a href="../../" class="logo">📊 Radar de Preços</a></div></header>
        <main class="container" style="padding: 40px 20px;">
            <article>
                <h1>{post_title}</h1>
                <p>Publicado em: {now.strftime('%d/%m/%Y %H:%M')}</p>
                <div class="content">
                    {offers_summary}
                    <p>Fique atento ao nosso radar para não perder nenhuma oportunidade!</p>
                </div>
                <div style="margin-top: 40px;">
                    <a href="../../" class="btn">Voltar para a Home</a>
                </div>
            </article>
        </main>
    </body>
    </html>
    """
    
    file_path = os.path.join(posts_dir, f"{post_slug}.html")
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Postagem gerada: {file_path}")

if __name__ == "__main__":
    generate_blog_content()
