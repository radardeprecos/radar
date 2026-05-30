import os
import json
from typing import List, Dict, Any
from logger import logger

def score_and_rank_products(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info(f"Processando score para {input_path}...")
    
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

    # Para produtos curados, garantimos que os campos de score existam
    for p in products:
        p["custom_score"] = p.get("custom_discount_pct", 0)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    logger.info(f"Ranqueados {len(products)} produtos com sucesso.")
    return products

if __name__ == "__main__":
    score_and_rank_products("data/raw_products.json", "data/scored_products.json")
