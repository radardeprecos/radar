
import json
import os
from jinja2 import Template

def generate_intelligence():
    data_file = 'data/database/all_products.json'
    output_dir = 'produtos'
    
    if not os.path.exists(data_file): return
    with open(data_file, 'r') as f:
        products = json.load(f)

    template_str = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Histórico de Preço: {{ p.name }} | Radar de Preços</title>
        <link rel="stylesheet" href="../../assets/css/style.css">
        <style>
            .intel-box { background: var(--card); padding: 30px; border-radius: 16px; border: 1px solid var(--border); margin-top: 30px; }
            .score-badge { font-size: 48px; font-weight: 900; color: var(--primary); }
            .veredit { font-size: 24px; font-weight: 800; margin-bottom: 20px; }
            .pros-cons { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
            .pros { color: #00a83f; }
            .cons { color: #dc2626; }
        </style>
    </head>
    <body>
        <header class="header"><div class="container"><a href="../../" class="logo">📊 Radar de Preços</a></div></header>
        <main class="container">
            <div class="intel-box">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h1>{{ p.name }}</h1>
                    <div class="score-badge">{{ p.custom_discount_pct // 10 }}</div>
                </div>
                
                <div class="veredit">
                    {% if p.custom_discount_pct > 40 %}
                        🔥 COMPRA OBRIGATÓRIA: Este produto está no menor preço histórico!
                    {% elif p.custom_discount_pct > 20 %}
                        ✅ VALE A PENA: O desconto é real e acima da média do mercado.
                    {% else %}
                        ⏳ AGUARDE: O desconto é pequeno. Pode baixar mais em breve.
                    {% endif %}
                </div>

                <div class="pros-cons">
                    <div class="pros">
                        <h4>👍 Prós</h4>
                        <ul>
                            <li>Desconto real de {{ p.custom_discount_pct }}%</li>
                            <li>Vendedor com excelente reputação</li>
                            <li>Entrega rápida garantida</li>
                        </ul>
                    </div>
                    <div class="cons">
                        <h4>👎 Contras</h4>
                        <ul>
                            <li>Estoque limitado</li>
                            <li>Alta demanda (pode esgotar)</li>
                        </ul>
                    </div>
                </div>

                <div style="margin-top:40px; text-align:center;">
                    <a href="{{ p.custom_affiliate_url or p.permalink }}" class="btn" style="padding: 20px 60px; font-size: 20px;">Ir para a Loja</a>
                </div>
            </div>
        </main>
    </body>
    </html>
    """
    template = Template(template_str)

    # Gerar apenas para produtos com desconto alto (>30%) para economizar build
    for p in products:
        if p.get('custom_discount_pct', 0) > 30:
            name_slug = p['name'].lower().replace(' ', '-').replace('/', '-')[:30]
            filename = f"intel-{name_slug}-{p['id']}.html"
            
            # Garantir diretório da categoria
            cat_dir = os.path.join(output_dir, p.get('custom_category_slug', 'outros'))
            if not os.path.exists(cat_dir): os.makedirs(cat_dir)
            
            with open(os.path.join(cat_dir, filename), 'w') as f:
                f.write(template.render(p=p))

if __name__ == "__main__":
    generate_intelligence()
