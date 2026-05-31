import json
import os
from datetime import datetime

def generate_blog_content():
    posts_dir = 'noticias/posts'
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)

    post_title = "Por que os preços de eletrônicos estão caindo em Junho de 2026"
    post_slug = "tendencias-precos-eletronicos-junho-2026"
    
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
        <article class="container">
            <h1>{post_title}</h1>
            <p>Análise de mercado exclusiva do Radar de Preços.</p>
        </article>
    </body>
    </html>
    """
    with open(os.path.join(posts_dir, f"{post_slug}.html"), 'w') as f:
        f.write(content)
generate_blog_content()
