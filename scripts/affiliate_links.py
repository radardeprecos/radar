import os
import json
from typing import List, Dict, Any
from logger import logger

def process_affiliate_links(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info(f"Processando links de afiliados de {input_path}...")
    
    if not os.path.exists(input_path):
        logger.warning(f"Arquivo {input_path} não encontrado.")
        products = []
    else:
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {input_path}: {e}")
            products = []

    # Para produtos curados, garantimos que os links existam
    for p in products:
        if "custom_affiliate_url" not in p:
            p["custom_affiliate_url"] = p.get("permalink", "")
            
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Links de afiliados processados para {len(products)} produtos.")
    return products

if __name__ == "__main__":
    process_affiliate_links("data/scored_products.json", "data/affiliate_products.json")
