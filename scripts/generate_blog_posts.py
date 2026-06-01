import os
import json
from datetime import datetime
from logger import logger

def generate_real_analysis(p):
    name = p.get('name', 'Produto')
    price = p.get('price', '0.00')
    discount = p.get('custom_discount_pct', 0)
    category = p.get('category', 'Geral')
    
    # Lógica de análise baseada na categoria
    analysis_points = {
        "Informatica": ["Desempenho em multitarefa", "Qualidade dos componentes", "Longevidade tecnológica"],
        "Beleza": ["Eficácia comprovada", "Custo por aplicação", "Reputação da marca"],
        "Games": ["Experiência imersiva", "Compatibilidade", "Valor de revenda"],
        "Casa": ["Durabilidade", "Design funcional", "Facilidade de manutenção"]
    }
    
    points = analysis_points.get(category, ["Qualidade geral", "Custo-benefício", "Garantia"])
    
    content = f"""
    <h2>🔍 Análise Profissional: {name}</h2>
    <p>O <strong>{name}</strong> se destaca hoje no mercado de {category} não apenas pelo preço, mas pela sua entrega técnica. Ao analisarmos o valor de <strong>R$ {price}</strong>, percebemos que ele está operando na faixa de preço de modelos de entrada, oferecendo recursos de modelos premium.</p>
    
    <h3>🚀 Pontos de Destaque</h3>
    <ul>
        {"".join([f"<li><strong>{pt}:</strong> Avaliado positivamente nos testes de estresse de mercado.</li>" for pt in points])}
    </ul>
    
    <h3>💰 Vale o Investimento?</h3>
    <p>Com um desconto real de {discount}%, o retorno sobre o investimento é imediato. No cenário econômico atual de 2026, produtos que mantêm sua qualidade e reduzem o preço são raros. O Radar de Preços recomenda a aquisição deste item para quem busca eficiência sem comprometer o orçamento.</p>
    
    <h3>📊 Veredito do Radar</h3>
    <p>Nossa nota para esta oferta é <strong>9.5/10</strong>. A combinação de estoque disponível no Mercado Livre com o link de afiliado seguro torna esta a melhor escolha do dia na categoria {category}.</p>
    """
    return content

def generate_blog_content():
    posts_dir = 'noticias/posts'
    os.makedirs(posts_dir, exist_ok=True)
    
    db_path = 'data/database/all_products.json'
    if not os.path.exists(db_path): return

    with open(db_path, 'r') as f:
        products = json.load(f)

    if not products: return

    # Gerar post para o Top 1
    products.sort(key=lambda x: x.get('custom_discount_pct', 0), reverse=True)
    p = products[0]
    
    post_slug = f"analise-detalhada-{p.get('id')}"
    file_path = os.path.join(posts_dir, f"{post_slug}.html")
    
    now = datetime.now()
    post_title = f"Review: {p.get('name')} - A Melhor Oferta de Hoje?"
    
    body = generate_real_analysis(p)
    
    content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>{post_title} | Radar de Preços</title>
        <link rel="stylesheet" href="../../assets/css/style.css">
        <meta name="description" content="Análise técnica completa do {p.get('name')}. Veja se vale a pena comprar hoje.">
    </head>
    <body>
        <header class="header"><div class="container"><a href="../../" class="logo">📊 Radar de Preços</a></div></header>
        <main class="container" style="padding: 40px 20px; max-width: 800px; margin: 0 auto;">
            <article>
                <h1>{post_title}</h1>
                <p style="color:#666">Publicado em {now.strftime('%d/%m/%Y')}</p>
                <hr style="margin:20px 0; border:0; border-top:1px solid #eee;">
                <div class="content">{body}</div>
                <div style="margin-top:40px; text-align:center; padding:30px; background:#f8fafc; border-radius:12px;">
                    <h3>🔥 Aproveite o Desconto de {p.get('custom_discount_pct')}%</h3>
                    <a href="{p.get('permalink')}" class="btn" style="background:#16a34a; color:white; padding:15px 30px; text-decoration:none; border-radius:8px; font-weight:bold; display:inline-block; margin-top:15px;">COMPRAR NO MERCADO LIVRE</a>
                </div>
            </article>
        </main>
    </body>
    </html>
    """
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Artigo de Elite gerado: {file_path}")

if __name__ == "__main__":
    generate_blog_content()
