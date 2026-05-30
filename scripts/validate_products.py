import os
import json
from typing import List, Dict, Any
from logger import logger

def validate_all_products(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info(f"Validando produtos de {input_path}...")
    
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

    # Para lista curada, a validação é implícita. 
    # Apenas garantimos que os campos básicos existem.
    valid_products = []
    for p in products:
        if p.get("id") and (p.get("name") or p.get("title")):
            valid_products.append(p)
            
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid_products, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Validação concluída. {len(valid_products)} de {len(products)} produtos aprovados.")
    return valid_products

if __name__ == "__main__":
    validate_all_products("data/affiliate_products.json", "data/validated_products.json")
