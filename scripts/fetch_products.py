import os
import json
from typing import Any, Dict, List
from logger import logger

def fetch_all_products() -> List[Dict[Dict[str, Any], Any]]:
    """
    Nova estratégia: Prioriza uma lista curada local para garantir estabilidade.
    Isso evita erros 403 e bloqueios de rede no GitHub Actions.
    """
    curated_path = "data/curated_products.json"
    
    if os.path.exists(curated_path):
        try:
            with open(curated_path, "r", encoding="utf-8") as f:
                products = json.load(f)
                logger.info(f"Sucesso: {len(products)} produtos carregados da lista curada.")
                return products
        except Exception as e:
            logger.error(f"Erro ao ler lista curada: {e}")
            
    logger.warning("Lista curada não encontrada ou vazia. Retornando lista vazia para o pipeline.")
    return []

if __name__ == "__main__":
    try:
        products = fetch_all_products()
        os.makedirs("data", exist_ok=True)
        with open("data/raw_products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        logger.info("Resultados salvos em data/raw_products.json")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        os.makedirs("data", exist_ok=True)
        with open("data/raw_products.json", "w") as f:
            json.dump([], f)
