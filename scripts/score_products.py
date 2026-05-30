import os
import json
from typing import List, Dict, Any
from logger import logger

def calculate_score(item: Dict[str, Any]) -> float:
    score = 0.0
    
    # 1. Desconto percentual (Fator mais importante)
    price = item.get("price") or 0.0
    original_price = item.get("originalPrice") or item.get("original_price") or price
    
    discount_pct = 0.0
    if original_price > price:
        discount_pct = ((original_price - price) / original_price) * 100.0
        
    # Salvar desconto calculado no item para facilidade
    item["custom_discount_pct"] = int(round(discount_pct))
    
    # Pontuação por desconto: até 40 pontos
    score += min(discount_pct * 1.2, 40.0)
    
    # 2. Reputação do Vendedor: até 20 pontos
    seller = item.get("seller", {})
    seller_reputation = seller.get("seller_reputation", {})
    power_seller_status = seller_reputation.get("power_seller_status")
    level_id = seller_reputation.get("level_id") # 5_green é o melhor
    
    if power_seller_status == "platinum":
        score += 20.0
    elif power_seller_status == "gold":
        score += 15.0
    elif power_seller_status == "silver":
        score += 10.0
        
    if level_id == "5_green":
        score += 10.0
    elif level_id == "4_light_green":
        score += 5.0
        
    # Limitar reputação a 20 pontos
    score = min(score, 60.0) # Se tiver platina + 5_green já ganha muito peso
    
    # 3. Frete Grátis: 10 pontos
    shipping = item.get("shipping", {})
    if shipping.get("free_shipping"):
        score += 10.0
        
    # 4. Vendas / Popularidade: até 15 pontos
    # A API pública às vezes traz "sold_quantity"
    sold_quantity = item.get("sold_quantity", 0)
    if sold_quantity > 500:
        score += 15.0
    elif sold_quantity > 100:
        score += 10.0
    elif sold_quantity > 10:
        score += 5.0
        
    # 5. Qualidade de dados (Tem imagem oficial de bom tamanho, título decente): até 15 pontos
    title = item.get("title", "")
    thumbnail = item.get("thumbnail", "")
    
    if len(title) > 20:
        score += 5.0
    if thumbnail.startswith("http"):
        score += 10.0
        
    return round(score, 2)

def score_and_rank_products(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info(f"Iniciando cálculo de score para produtos em {input_path}...")
    if not os.path.exists(input_path):
        logger.error(f"Arquivo de entrada {input_path} não encontrado!")
        return []
        
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar {input_path}: {e}")
        return []
        
    if not products:
        logger.warning("Nenhum produto para calcular score.")
        # Criar arquivo vazio para não quebrar o pipeline downstream
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    scored_products = []
    for item in products:
        score = calculate_score(item)
        item["custom_score"] = score
        scored_products.append(item)
        
    # Ordenar por score decrescente
    scored_products.sort(key=lambda x: x["custom_score"], reverse=True)
    
    logger.info(f"Ranqueados {len(scored_products)} produtos com sucesso.")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scored_products, f, ensure_ascii=False, indent=2)
        
    return scored_products

if __name__ == "__main__":
    score_and_rank_products("data/raw_products.json", "data/scored_products.json")
