import os
import re
from bs4 import BeautifulSoup

base_dir = '/home/ubuntu/radar_repo'
ml_id = 'radar041-20'
amz_id = "radar041-20"

def audit_and_fix(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return 'OK'
    
    soup = BeautifulSoup(content, 'html.parser')
    modified = False
    
    # 1. Pente fino em IMAGENS (Remover se não tiver imagem ou se for placeholder)
    if '/ofertas/' in file_path:
        images = soup.find_all('img')
        valid_image = False
        for img in images:
            src = img.get('src', '')
            if src and 'http' in src and 'placeholder' not in src.lower():
                valid_image = True
                break
        
        if not valid_image:
            print(f"DELETANDO (Sem Imagem): {file_path}")
            return 'DELETE'

    # 2. Pente fino em AFILIADOS (Forçar injeção em todos os links externos)
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        if 'mercadolivre.com' in href:
            if ml_id not in href:
                connector = '&' if '?' in href else '?'
                # Se já tiver matt_tool de outro, substituir
                if 'matt_tool=' in href:
                    a['href'] = re.sub(r'matt_tool=[^&]*', f'matt_tool={ml_id}', href)
                else:
                    a['href'] = href + f"{connector}matt_tool={ml_id}"
                modified = True
        
        elif 'amazon.com.br' in href:
            if amz_id not in href:
                if 'tag=' in href:
                    a['href'] = re.sub(r'tag=[^&]*', f'tag={amz_id}', href)
                else:
                    connector = '&' if '?' in href else '?'
                    a['href'] = href + f"{connector}tag={amz_id}"
                modified = True

    # 3. Pente fino em LINKS QUEBRADOS (404 internos)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'):
            continue
        
        # Verificar se o arquivo existe
        target = href.split('#')[0].split('?')[0].strip('/')
        if not target or target == 'index.html': continue
        
        # Ajuste para caminhos relativos de ofertas
        if '/ofertas/' in file_path and target.startswith('../../'):
            check_path = os.path.join(base_dir, target.replace('../../', ''))
        elif '/ofertas/' in file_path and target.startswith('../'):
            check_path = os.path.join(os.path.dirname(file_path), target)
        else:
            check_path = os.path.join(base_dir, target)

        if not (os.path.exists(check_path) or os.path.exists(check_path + '.html') or 
                (os.path.isdir(check_path) and os.path.exists(os.path.join(check_path, 'index.html')))):
            # Link quebrado - remover o link mas manter o texto
            a.replace_with(a.get_text())
            modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return 'FIXED'
    return 'OK'

def run():
    fixed = 0
    deleted = 0
    for root, dirs, files in os.walk(base_dir):
        if any(x in root for x in ['.git', 'scripts', 'assets']): continue
        for file in files:
            if file.endswith('.html'):
                res = audit_and_fix(os.path.join(root, file))
                if res == 'FIXED': fixed += 1
                elif res == 'DELETE':
                    os.remove(os.path.join(root, file))
                    deleted += 1
    print(f"Pente Fino Finalizado: {fixed} corrigidos, {deleted} deletados.")

if __name__ == "__main__":
    run()
