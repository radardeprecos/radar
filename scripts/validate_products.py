import json
import os
import sys
from logger import logger

def validate(input_p):
    # ERRO CONTROLADO PARA TESTE DE AUTO-CURA
    if os.environ.get("TEST_FAIL") == "true":
        logger.error("!!! TESTE DE FALHA CONTROLADA ATIVADO !!!")
        raise FileNotFoundError("Erro simulado: Arquivo 'config_secreta.json' não encontrado para validação.")

    if not os.path.exists(input_p):
        logger.warning(f"Arquivo {input_p} não encontrado.")
        return False
        
    with open(input_p, "r", encoding="utf-8") as f:
        products = json.load(f)
        
    logger.info(f"Validando integridade de {len(products)} produtos...")
    # Lógica de validação simplificada para o teste
    valid_products = [p for p in products if "id" in p and "price" in p]
    
    logger.info(f"Validação concluída: {len(valid_products)}/{len(products)} produtos aprovados.")
    return len(valid_products) == len(products)

if __name__ == "__main__":
    success = validate("data/new_offers.json")
    if not success:
        sys.exit(1)
