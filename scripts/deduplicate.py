
import os
import json
from logger import logger

def process(input_p: str, output_p: str):
    if not os.path.exists(input_p):
        logger.warning(f"Arquivo de entrada {input_p} não encontrado.")
        products = []
    else:
        with open(input_p, "r", encoding="utf-8") as f:
            products = json.load(f)
    
    total_original = len(products)
    unique_products = {}
    
    # Ordenar por maior desconto e menor preço para garantir que a melhor oferta sobreviva
    products.sort(key=lambda x: (x.get('custom_discount_pct', 0), -float(x.get('price', 0))), reverse=True)

    for p in products:
        p_id = p.get('id')
        p_url = p.get('permalink') or p.get('url')
        p_title_price = f"{p.get('name') or p.get('title')}_{p.get('price')}"
        
        # Chaves de deduplicação
        if p_id and p_id in unique_products:
            continue
        
        # Verificar se já existe um produto com a mesma URL ou mesmo Título+Preço
        is_duplicate = False
        for up in unique_products.values():
            if (p_url and (up.get('permalink') == p_url or up.get('url') == p_url)) or \
               (f"{up.get('name') or up.get('title')}_{up.get('price')}" == p_title_price):
                is_duplicate = True
                break
        
        if not is_duplicate and p_id:
            unique_products[p_id] = p

    final_products = list(unique_products.values())
    total_removed = total_original - len(final_products)
    
    logger.info(f"Deduplicação concluída: {total_original} produtos processados, {total_removed} duplicados removidos.")
    
    os.makedirs(os.path.dirname(output_p), exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        json.dump(final_products, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process("data/validated_products.json", "data/new_offers.json")
