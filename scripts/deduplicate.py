import os
import json
import unicodedata
import hashlib
from logger import logger

HISTORY_FILE = "data/history/posted_products.json"

def slugify(text: str) -> str:
    if not text: return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().replace(' ', '-')
    return ''.join(c for c in text if c.isalnum() or c == '-')

def get_content_hash(p: dict) -> str:
    """Gera um hash baseado no nome e preço para detectar mudanças reais."""
    content = f"{p.get('name', '')}{p.get('price', 0)}"
    return hashlib.md5(content.encode()).hexdigest()

def process(input_p: str, output_p: str):
    if not os.path.exists(input_p):
        logger.warning(f"Arquivo de entrada {input_p} não encontrado.")
        products = []
    else:
        with open(input_p, "r", encoding="utf-8") as f:
            products = json.load(f)

    # Carregar histórico de IDs já postados para evitar spam
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)

    total_original = len(products)
    unique_products = {}
    
    # Ordenação por qualidade (desconto)
    products.sort(key=lambda x: (x.get('custom_discount_pct', 0), -float(x.get('price', 0))), reverse=True)

    for p in products:
        p_id = str(p.get('id', ''))
        if not p_id: continue
        
        p_name = p.get('name', '')
        p_price = float(p.get('price', 0))
        p_slug = slugify(p_name)
        p_hash = get_content_hash(p)

        # TRAVA 1: ID Único nesta rodada
        if p_id in unique_products: continue

        # TRAVA 2: Conteúdo idêntico já postado no histórico (mesmo ID e mesmo Preço)
        if p_id in history and history[p_id].get('hash') == p_hash:
            # logger.info(f"Pulando {p_id} - Já postado com este preço recentemente.")
            continue

        # TRAVA 3: Deduplicação semântica (mesmo slug e preço similar)
        is_duplicate = False
        for up in unique_products.values():
            if slugify(up.get('name', '')) == p_slug:
                up_price = float(up.get('price', 0))
                if up_price > 0 and (abs(p_price - up_price) / up_price) < 0.01:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_products[p_id] = p
            # Atualizar histórico
            history[p_id] = {
                "last_posted": datetime.now().isoformat() if 'datetime' in globals() else "2026-06-01",
                "hash": p_hash,
                "price": p_price
            }

    final_products = list(unique_products.values())
    
    # Salvar histórico atualizado
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    logger.info(f"Blindagem concluída: {total_original} -> {len(final_products)} (Removidos: {total_original - len(final_products)})")
    
    os.makedirs(os.path.dirname(output_p), exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        json.dump(final_products, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    from datetime import datetime
    process("data/validated_products.json", "data/new_offers.json")
