import os
import json
import requests
import concurrent.futures
from typing import List, Dict, Any
from logger import logger

TIMEOUT = 10

def validate_single_url(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        # Fazer requisição HEAD ou GET leve para validar HTTP 200
        response = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        if response.status_code == 200:
            return True
        # Se HEAD falhar com 405 ou outro código, tentar GET leve
        response = requests.get(url, timeout=TIMEOUT, stream=True)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Falha ao validar URL {url}: {e}")
        return False

def validate_product(item: Dict[str, Any]) -> bool:
    # 1. Validar imagem oficial
    thumbnail = item.get("thumbnail", "")
    # Substituir por imagem de alta resolução se possível
    image_url = thumbnail.replace("-I.jpg", "-O.jpg").replace("-I.webp", "-O.webp")
    if not image_url.startswith("http"):
        # Tentar usar pictures da API se disponível
        pictures = item.get("pictures", [])
        if pictures:
            image_url = pictures[0].get("secure_url", "")
            
    if not image_url:
        logger.warning(f"Produto {item.get('id')} sem imagem válida.")
        return False
        
    item["custom_image_url"] = image_url
    
    # Validar imagem HTTP 200
    if not validate_single_url(image_url):
        logger.warning(f"Imagem do produto {item.get('id')} retornou erro HTTP ou está inacessível: {image_url}")
        return False
        
    # 2. Validar link de afiliado / redirecionamento do produto
    aff_url = item.get("custom_affiliate_url", "")
    if not aff_url:
        logger.warning(f"Produto {item.get('id')} sem URL de afiliado.")
        return False
        
    # Como o link de afiliado oficial do ML redireciona, validamos se responde corretamente
    if not validate_single_url(aff_url):
        logger.warning(f"URL de afiliado do produto {item.get('id')} inválida ou inacessível: {aff_url}")
        return False
        
    return True

def validate_all_products(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info(f"Validando produtos de {input_path}...")
    if not os.path.exists(input_path):
        logger.error(f"Arquivo {input_path} não encontrado!")
        return []
        
    with open(input_path, "r", encoding="utf-8") as f:
        products = json.load(f)
        
    valid_products = []
    
    # Validar em paralelo para acelerar o processo sem travar o pipeline
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(validate_product, products)
        
        for item, is_valid in zip(products, results):
            if is_valid:
                valid_products.append(item)
            else:
                logger.info(f"Produto {item.get('id')} - {item.get('title')} REJEITADO na validação.")
                
    logger.info(f"Validação concluída. {len(valid_products)} de {len(products)} produtos aprovados.")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid_products, f, ensure_ascii=False, indent=2)
        
    return valid_products

if __name__ == "__main__":
    validate_all_products("data/affiliate_products.json", "data/validated_products.json")
