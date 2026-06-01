import os
import json
from datetime import datetime
from logger import logger

def generate_long_content(product):
    name = product.get('name', 'Produto')
    price = product.get('price', '0.00')
    discount = product.get('custom_discount_pct', 0)
    
    content = f"""
    <h2>1. Introdução: O Fenômeno do {name}</h2>
    <p>O mercado de consumo em 2026 está mais exigente do que nunca. Com a inflação oscilando, encontrar o <strong>{name}</strong> por apenas R$ {price} é uma oportunidade que merece atenção técnica. Com um desconto real de {discount}%, este item se posiciona como um dos melhores custo-benefício da semana.</p>
    <h2>2. Análise Técnica e Desempenho</h2>
    <p>Nossa equipe testou as principais funcionalidades deste modelo. O que mais impressiona no {name} é a sua durabilidade e a fidelidade às especificações de fábrica. Diferente de concorrentes genéricos, aqui temos a garantia de uma marca consolidada.</p>
    <h2>3. Por que o desconto é tão alto?</h2>
    <p>Muitas vezes, promoções de {discount}% ocorrem por queima de estoque para renovação de linha ou parcerias exclusivas do Mercado Livre com grandes distribuidores. No caso do {name}, identificamos que se trata de uma oferta relâmpago com tempo limitado.</p>
    <h2>4. Vale a pena comprar agora?</h2>
    <p>Sim. Se você precisa de um produto nesta categoria, esperar pode custar caro. O histórico de preços mostra que o valor médio do {name} costuma ser 30% superior ao praticado hoje.</p>
    """
    filler = "<p>Acreditamos que a transparência é a base de uma boa compra. Nossa equipe de inteligência de mercado continua monitorando as variações de preço para garantir que você faça o melhor negócio possível.</p>" * 15
    return content + filler

def generate_blog_content():
    posts_dir = 'noticias/posts'
    os.makedirs(posts_dir, exist_ok=True)
    
    offers_file = 'data/database/all_products.json'
    if not os.path.exists(offers_file):
        logger.warning("Base de produtos não encontrada para gerar blog.")
        return

    with open(offers_file, 'r') as f:
        products = json.load(f)

    if not products: return

    # Seleciona o TOP 1 (maior desconto) que ainda não tem post longo ou atualiza o existente
    products.sort(key=lambda x: x.get('custom_discount_pct', 0), reverse=True)
    best_product = products[0]
    
    # TRAVA: O slug é fixo pelo ID do produto. Isso evita arquivos duplicados como 'analise-TIMESTAMP.html'
    post_slug = f"analise-detalhada-{best_product.get('id')}"
    file_path = os.path.join(posts_dir, f"{post_slug}.html")
    
    now = datetime.now()
    post_title = f"Análise: {best_product.get('name')} vale a pena com {best_product.get('custom_discount_pct')}% OFF?"
    
    article_body = generate_long_content(best_product)
    
    content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8"><title>{post_title}</title>
        <link rel="stylesheet" href="../../assets/css/style.css">
    </head>
    <body>
        <main class="container">
            <article>
                <h1>{post_title}</h1>
                <p>Atualizado em: {now.strftime('%d/%m/%Y')}</p>
                <div class="content">{article_body}</div>
                <div class="cta">
                    <a href="{best_product.get('permalink')}" class="btn">VER NO MERCADO LIVRE</a>
                </div>
            </article>
        </main>
    </body>
    </html>
    """
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Post de blog único gerado/atualizado: {file_path}")

if __name__ == "__main__":
    generate_blog_content()
