import os
from bs4 import BeautifulSoup
import re

base_dir = '/home/ubuntu/radar_repo'

def clean_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    modified = False
    
    # 1. Remover produtos sem imagem ou com imagem quebrada
    # Geralmente em cards de produtos
    product_cards = soup.find_all(class_=re.compile(r'product|card|item', re.I))
    for card in product_cards:
        img = card.find('img')
        if not img or not img.get('src') or 'placeholder' in img.get('src').lower():
            card.decompose()
            modified = True
            continue
            
    # 2. Verificar links internos quebrados
    links = soup.find_all('a', href=True)
    for link in links:
        href = link['href']
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
            
        # Limpar href para verificar arquivo
        clean_href = href.split('#')[0].split('?')[0].strip('/')
        if not clean_href: continue
        
        full_path = os.path.join(base_dir, clean_href)
        if not (os.path.exists(full_path) or os.path.exists(full_path + '.html') or 
                (os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, 'index.html')))):
            # Se o link está quebrado, podemos remover o link mas manter o texto, ou remover o elemento
            # Para AdSense, melhor remover links que levam a 404
            link.replace_with(link.get_text())
            modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    return False

def run_deep_clean():
    count = 0
    for root, dirs, files in os.walk(base_dir):
        if 'scripts' in root or '.git' in root: continue
        for file in files:
            if file.endswith('.html'):
                if clean_html_file(os.path.join(root, file)):
                    count += 1
    print(f"Limpeza profunda concluída em {count} arquivos.")

if __name__ == "__main__":
    run_deep_clean()
