import os
import json
import requests
from typing import List, Dict, Any
from logger import logger

AFILIADO_ID = os.getenv("ML_AFILIADO_ID", "vendas0nline")
ACCESS_TOKEN = (
    os.getenv("MERCADOLIBRE_ACCESS_TOKEN")
    or os.getenv("ML_ACCESS_TOKEN")
    or os.getenv("ML_API_ACCESS_TOKEN")
)

def generate_official_affiliate_link(permalink: str) -> str:
    """
    Gera link rastreado de afiliado usando o formato social oficial do Mercado Livre.
    Se houver token e API oficial de afiliados disponível, pode ser expandida aqui.
    O formato social/vendas0nline?item=ID é o padrão oficial aceito pelo programa de afiliados.
    """
    if not permalink:
        return ""
        
    # Extrair ID do produto a partir do permalink ou usar formato direto
    # Exemplo: MLB3052590153
    parts = permalink.split("/")
    item_id = ""
    for part in parts:
        if "MLB" in part:
            # Pegar a parte que contém MLB e os números
            subparts = part.split("-")
            for sp in subparts:
                if sp.startswith("MLB") and sp[3:].isdigit():
                    item_id = sp
                    break
            if item_id:
                break
                
    if not item_id:
        # Tentar extrair de outra forma
        import re
        match = re.search(r"MLB-?(\d+)", permalink)
        if match:
            item_id = f"MLB{match.group(1)}"
            
    if item_id:
        # Retornar o link de afiliado oficial do Mercado Livre
        return f"https://www.mercadolivre.com.br/social/{AFILIADO_ID}?item={item_id}"
        
    # Fallback robusto adicionando tags de tracking ao permalink original
    connector = "&" if "?" in permalink else "?"
    return f"{permalink}{connector}utm_source=affiliate&utm_medium=link&utm_campaign={AFILIADO_ID}"

def process_affiliate_links(input_path: str, output_path: str) -> List[Dict[str, Any]]:
    logger.info(f"Processando links de afiliados de {input_path}...")
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
        logger.warning("Nenhum produto para processar links de afiliados.")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    for item in products:
        permalink = item.get("permalink", "")
        aff_link = generate_official_affiliate_link(permalink)
        item["custom_affiliate_url"] = aff_link
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Links de afiliados processados para {len(products)} produtos.")
    return products

if __name__ == "__main__":
    process_affiliate_links("data/scored_products.json", "data/affiliate_products.json")
