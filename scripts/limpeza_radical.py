import os
import json
import requests
import re
from bs4 import BeautifulSoup

db_path = '/home/ubuntu/radar_repo/data/database/all_products.json'
base_dir = '/home/ubuntu/radar_repo'
ml_id = 'vendas0nline'
amz_id = 'vendas0nline'

def is_valid_image(url):
    if not url or 'placeholder' in url.lower() or 'none' in url.lower():
        return False
    try:
        # User-agent para evitar bloqueios simples
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=10, headers=headers, stream=True)
        # Verificar se é uma imagem real pelo content-type
        content_type = response.headers.get('Content-Type', '')
        return response.status_code == 200 and 'image' in content_type
    except:
        return False

def is_monetized(product):
    url = product.get('custom_affiliate_url', '') or product.get('permalink', '')
    if 'mercadolivre.com' in url and ml_id in url:
        return True
    if 'amazon.com.br' in url and amz_id in url:
        return True
    return False

def run_radical_clean():
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado.")
        return
    
    with open(db_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    initial_count = len(products)
    clean_products = []
    
    print(f"Auditoria radical iniciada em {initial_count} produtos...")
    
    for p in products:
        img_url = p.get('image') or p.get('thumbnail')
        
        # Critério 1: Tem imagem válida?
        if not is_valid_image(img_url):
            print(f"REMOVENDO (Imagem Inválida): {p.get('name')}")
            continue
            
        # Critério 2: Está monetizado?
        # Se não estiver, vamos tentar injetar o ID agora
        url = p.get('custom_affiliate_url', '') or p.get('permalink', '')
        if 'mercadolivre.com' in url and ml_id not in url:
            connector = '&' if '?' in url else '?'
            p['custom_affiliate_url'] = url + f"{connector}matt_tool={ml_id}"
        elif 'amazon.com.br' in url and amz_id not in url:
            connector = '&' if '?' in url else '?'
            p['custom_affiliate_url'] = url + f"{connector}tag={amz_id}"
            
        clean_products.append(p)
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(clean_products, f, ensure_ascii=False, indent=2)
    
    print(f"Limpeza concluída. {len(clean_products)} produtos restantes.")
    return [str(p.get('id')) for p in clean_products]

if __name__ == "__main__":
    valid_ids = run_radical_clean()
    
    # Limpar arquivos HTML de ofertas que não são mais válidas
    ofertas_dir = os.path.join(base_dir, 'ofertas')
    for root, dirs, files in os.walk(ofertas_dir):
        for file in files:
            if file.endswith('.html'):
                match = re.search(r'(MLB\d+)', file)
                if match:
                    pid = match.group(1)
                    if pid not in "".join(valid_ids):
                        os.remove(os.path.join(root, file))
                        print(f"HTML Deletado: {file}")
