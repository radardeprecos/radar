import os
import re
from bs4 import BeautifulSoup

base_dir = '/home/ubuntu/radar_repo'
ml_id = 'vendas0nline'
amz_id = 'vendas0nline'

def audit_and_fix(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    modified = False
    
    # 1. Remover produtos sem foto ou com fotos quebradas
    # Procuramos por containers de produtos (cards)
    for card in soup.find_all(class_=re.compile(r'product|card|item', re.I)):
        img = card.find('img')
        if not img or not img.get('src') or 'placeholder' in img.get('src').lower() or 'none' in img.get('src').lower():
            card.decompose()
            modified = True
            continue
            
    # 2. Garantir IDs de afiliados em todos os links de ofertas
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Mercado Livre
        if 'mercadolivre.com' in href or 'mercadolivre.com.br' in href:
            if ml_id not in href:
                # Se for um link direto de produto, podemos tentar anexar o ID
                if 'MLB-' in href or 'MLB' in href:
                    connector = '&' if '?' in href else '?'
                    a['href'] = href + f"{connector}affiliate_id={ml_id}"
                    modified = True
        
        # Amazon
        elif 'amazon.com.br' in href:
            if amz_id not in href:
                connector = '&' if '?' in href else '?'
                a['href'] = href + f"{connector}tag={amz_id}"
                modified = True

    # 3. Remover links internos quebrados (404)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        
        clean_href = href.split('#')[0].split('?')[0].strip('/')
        if not clean_href: continue
        
        full_path = os.path.join(base_dir, clean_href)
        if not (os.path.exists(full_path) or os.path.exists(full_path + '.html') or 
                (os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, 'index.html')))):
            # Remover o link mas manter o texto para não quebrar o layout
            a.replace_with(a.get_text())
            modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    return False

def run_pente_fino():
    files_fixed = 0
    for root, dirs, files in os.walk(base_dir):
        if 'scripts' in root or '.git' in root or 'assets' in root: continue
        for file in files:
            if file.endswith('.html'):
                if audit_and_fix(os.path.join(root, file)):
                    files_fixed += 1
    print(f"Pente fino concluído: {files_fixed} arquivos corrigidos.")

if __name__ == "__main__":
    run_pente_fino()
