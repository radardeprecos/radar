import os
import json
import requests
import re
from bs4 import BeautifulSoup

db_path = '/home/ubuntu/radar_repo/data/database/all_products.json'
base_dir = '/home/ubuntu/radar_repo'
ml_id = 'radar041-20'
amz_id = 'radar041-20'

def check_image(url):
    if not url or 'placeholder' in url.lower():
        return False
    try:
        # Tentar carregar a imagem com timeout curto
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def clean_database():
    if not os.path.exists(db_path):
        return []
    
    with open(db_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    initial_count = len(products)
    valid_products = []
    removed_names = []
    
    print(f"Iniciando auditoria de {initial_count} produtos...")
    
    for p in products:
        img_url = p.get('image') or p.get('thumbnail')
        if check_image(img_url):
            valid_products.append(p)
        else:
            removed_names.append(p.get('name', 'Sem Nome'))
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(valid_products, f, ensure_ascii=False, indent=2)
    
    print(f"Limpeza de Banco de Dados concluída:")
    print(f"- Produtos removidos: {initial_count - len(valid_products)}")
    for name in removed_names:
        print(f"  > Removido: {name}")
    return [p.get('id') for p in valid_products]

def clean_html_files(valid_ids):
    # Remover arquivos HTML de ofertas que não estão mais no banco de dados
    ofertas_dir = os.path.join(base_dir, 'ofertas')
    for root, dirs, files in os.walk(ofertas_dir):
        for file in files:
            if file.endswith('.html'):
                # Extrair o ID (MLB...) do nome do arquivo
                match = re.search(r'(MLB\d+)', file)
                if match:
                    product_id = match.group(1)
                    if product_id not in str(valid_ids):
                        os.remove(os.path.join(root, file))
                        print(f"Arquivo HTML removido: {file}")

if __name__ == "__main__":
    valid_ids = clean_database()
    clean_html_files(valid_ids)
