import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from logger import logger

def check_url(url):
    if not url or not url.startswith("http"):
        return False
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        # GET para evitar 405 do Mercado Livre, stream=True para economizar banda
        response = requests.get(url, headers=headers, timeout=5, stream=True)
        return response.status_code == 200
    except:
        return False

def process(input_p: str, output_p: str):
    if not os.path.exists(input_p):
        logger.error(f"Arquivo de entrada não encontrado: {input_p}")
        return

    with open(input_p, "r", encoding="utf-8") as f:
        products = json.load(f)

    logger.info(f"Validando integridade de {len(products)} produtos...")

    def validate_product(p):
        img_url = p.get("image") or p.get("thumbnail")
        aff_url = p.get("affiliate_url") or p.get("permalink")
        
        # Validar imagem
        if not img_url:
            return None
        if not check_url(img_url):
            logger.warning(f"Removendo produto {p.get('id')} por imagem quebrada.")
            return None
            
        # Validar link de afiliado
        if not aff_url:
            return None
        if not check_url(aff_url):
            logger.warning(f"Removendo produto {p.get('id')} por link quebrado.")
            return None
            
        return p

    with ThreadPoolExecutor(max_workers=10) as executor:
        valid_products = list(filter(None, executor.map(validate_product, products)))

    os.makedirs(os.path.dirname(output_p), exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        json.dump(valid_products, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Validação concluída: {len(valid_products)}/{len(products)} produtos aprovados.")

if __name__ == "__main__":
    process("data/affiliate_products.json", "data/validated_products.json")
