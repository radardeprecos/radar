import os
import json
from typing import List, Dict, Any
from logger import logger

def deduplicate_products(validated_path: str, published_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info("Iniciando processo de anti-duplicação...")
    
    if not os.path.exists(validated_path):
        logger.error(f"Arquivo de validados {validated_path} não encontrado!")
        return []
        
    with open(validated_path, "r", encoding="utf-8") as f:
        validated_products = json.load(f)
        
    published_ids = set()
    if os.path.exists(published_path):
        try:
            with open(published_path, "r", encoding="utf-8") as f:
                published_products = json.load(f)
                for item in published_products:
                    published_ids.add(item.get("id"))
            logger.info(f"Carregados {len(published_ids)} IDs de produtos já publicados anteriormente.")
        except Exception as e:
            logger.error(f"Erro ao carregar histórico de publicados: {e}")
            
    new_to_publish = []
    for item in validated_products:
        item_id = item.get("id")
        if item_id in published_ids:
            logger.info(f"Produto {item_id} já publicado anteriormente. Ignorando.")
            continue
        new_to_publish.append(item)
        
    logger.info(f"Total de novos produtos prontos para publicação única: {len(new_to_publish)}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(new_to_publish, f, ensure_ascii=False, indent=2)
        
    return new_to_publish

if __name__ == "__main__":
    deduplicate_products("data/validated_products.json", "data/published.json", "data/new_offers.json")
