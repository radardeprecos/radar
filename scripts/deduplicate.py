import os
import json
from typing import List, Dict, Any
from logger import logger

def deduplicate_products(validated_path: str, published_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info("Iniciando processo de anti-duplicação...")
    
    if not os.path.exists(validated_path):
        logger.warning(f"Arquivo {validated_path} não encontrado.")
        products = []
    else:
        try:
            with open(validated_path, "r", encoding="utf-8") as f:
                products = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar {validated_path}: {e}")
            products = []

    # Para lista curada, apenas repassamos para garantir que apareçam no site
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Total de produtos prontos para publicação: {len(products)}")
    return products

if __name__ == "__main__":
    deduplicate_products("data/validated_products.json", "data/published.json", "data/new_offers.json")
