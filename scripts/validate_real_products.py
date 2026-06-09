import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from logger import logger

def check_url(url):
    try:
        response = requests.get(url, timeout=10, stream=True)
        return response.status_code in [200, 405]
    except:
        return False

def validate_product(product):
    # Campos obrigatórios
    required = ['id', 'name', 'price', 'permalink', 'image', 'custom_category_slug']
    for field in required:
        if not product.get(field):
            return None
    
    # Validar Imagem e Link
    if not check_url(product['image']):
        return None
    
    # Nota: Validar o permalink pode ser lento, vamos focar na imagem que é crítica para UI
    # e assumir que o permalink do ML é estável se o ID for válido.
    
    return product

def main():
    input_files = [
        'data/database/all_products.json',
        'data/curated_products.json',
        'data/products/offers.json',
        'data/validated_products.json'
    ]
    output_file = 'data/database/validated_200_products.json'
    
    products = []
    seen_ids = set()
    for f_path in input_files:
        if os.path.exists(f_path):
            with open(f_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for p in data:
                    if p.get('id') not in seen_ids:
                        products.append(p)
                        seen_ids.add(p['id'])

    logger.info(f"Iniciando validação de {len(products)} produtos...")
    
    validated = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(validate_product, products))
        
    for p in results:
        if p:
            validated.append(p)
            if len(validated) >= 200:
                break

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(validated, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Sucesso: {len(validated)} produtos reais validados e salvos.")

if __name__ == "__main__":
    main()
