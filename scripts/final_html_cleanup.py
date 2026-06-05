import os
import re

base_dir = '/home/ubuntu/radardeprecos.github.io/radar/ofertas'

def clean_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 1. Remover R$ 0,00 e spans relacionados
    if 'R$ 0,00' in content:
        # Remover spans de preço antigo
        content = re.sub(r'<span class="old-price">.*?R\$ 0,00.*?</span>', '', content, flags=re.DOTALL)
        # Remover linhas de tabela
        content = re.sub(r'<tr><td>Preço Original</td><td>R\$ 0,00</td></tr>', '', content)
        # Remover no script JS
        content = re.sub(r'const oldPrice = parseFloat\("R\$ 0,00".*?\);', 'const oldPrice = currentPrice;', content)
        modified = True
        
    # 2. Breadcrumbs inteligentes
    # Extrair categoria do caminho: ofertas/categoria/arquivo.html
    parts = os.path.relpath(file_path, base_dir).split(os.sep)
    if len(parts) >= 2:
        category_slug = parts[0]
        category_name = category_slug.replace('-', ' ').capitalize()
        
        # Substituir o link genérico do breadcrumb
        breadcrumb_pattern = r'<a href="\.\./\.\./categorias/.*?/index\.html">Categoria</a>'
        new_breadcrumb = f'<a href="../../ofertas/{category_slug}/index.html">{category_name}</a>'
        
        if re.search(breadcrumb_pattern, content):
            content = re.sub(breadcrumb_pattern, new_breadcrumb, content)
            modified = True
        elif 'Categoria' in content and '../../categorias/' in content:
             # Fallback para outros formatos de link de categoria
             content = re.sub(r'<a href=".*?">Categoria</a>', new_breadcrumb, content)
             modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

count = 0
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.html') and f != 'index.html':
            if clean_html(os.path.join(root, f)):
                count += 1

print(f"Limpeza final concluída em {count} arquivos.")
