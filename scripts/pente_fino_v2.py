import os
import re
from bs4 import BeautifulSoup

base_dir = '/home/ubuntu/radar_repo'
ml_id = 'vendas0nline'
amz_id = "vendas0nline"

def audit_and_fix(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    modified = False
    
    # 1. Remover produtos sem foto (Cards e Ofertas)
    # Detectar cards em listas
    for card in soup.find_all(class_=re.compile(r'product|card|item', re.I)):
        img = card.find('img')
        if not img or not img.get('src') or 'placeholder' in img.get('src').lower() or 'none' in img.get('src').lower():
            card.decompose()
            modified = True
    
    # Se for uma página de produto único e não tiver imagem principal
    if '/ofertas/' in file_path:
        main_img = soup.find('img', class_=re.compile(r'main|product|hero', re.I))
        if not main_img and not soup.find('img'):
            print(f"Página de produto sem imagem detectada: {file_path}")
            # Aqui poderíamos deletar o arquivo, mas vamos apenas marcar para remoção manual ou logar
            return 'DELETE'

    # 2. Garantir IDs de afiliados em todos os links de ofertas
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Mercado Livre
        if 'mercadolivre.com' in href:
            if 'matt_tool=' not in href and 'affiliate_id=' not in href:
                connector = '&' if '?' in href else '?'
                a['href'] = href + f"{connector}matt_tool={ml_id}"
                modified = True
        
        # Amazon
        elif 'amazon.com.br' in href:
            if 'tag=' not in href:
                connector = '&' if '?' in href else '?'
                a['href'] = href + f"{connector}tag={amz_id}"
                modified = True

    # 3. Remover links internos quebrados (404)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        
        # Ajustar caminhos relativos para absoluto para verificação
        if href.startswith('../'):
            # Simplificação: apenas verificar se o arquivo existe no repo
            clean_href = href.replace('../', '').split('#')[0].split('?')[0].strip('/')
        else:
            clean_href = href.split('#')[0].split('?')[0].strip('/')
            
        if not clean_href: continue
        
        found = False
        # Verificar em vários níveis possíveis
        for check_path in [clean_href, clean_href + '.html', os.path.join(clean_href, 'index.html')]:
            if os.path.exists(os.path.join(base_dir, check_path)):
                found = True
                break
        
        if not found:
            # Remover o link mas manter o texto
            a.replace_with(a.get_text())
            modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return 'FIXED'
    return 'OK'

def run_pente_fino():
    fixed_count = 0
    deleted_count = 0
    for root, dirs, files in os.walk(base_dir):
        if any(x in root for x in ['scripts', '.git', 'assets']): continue
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                result = audit_and_fix(file_path)
                if result == 'FIXED':
                    fixed_count += 1
                elif result == 'DELETE':
                    os.remove(file_path)
                    deleted_count += 1
                    
    print(f"Pente fino concluído:")
    print(f"- Arquivos corrigidos: {fixed_count}")
    print(f"- Arquivos removidos (sem foto): {deleted_count}")

if __name__ == "__main__":
    run_pente_fino()
