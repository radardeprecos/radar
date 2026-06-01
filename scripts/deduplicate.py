import os
import json
import unicodedata
import hashlib
from datetime import datetime
from logger import logger

HISTORY_FILE = "data/history/posted_products.json"

def slugify(text: str) -> str:
    if not text: return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower().replace(' ', '-')
    return ''.join(c for c in text if c.isalnum() or c == '-')

def get_content_hash(p: dict) -> str:
    # Hash focado em ID e Preço para detectar atualizações
    content = f"{p.get('id', '')}{p.get('price', 0)}"
    return hashlib.md5(content.encode()).hexdigest()

def process(input_p: str, output_p: str):
    if not os.path.exists(input_p):
        products = []
    else:
        with open(input_p, "r", encoding="utf-8") as f:
            products = json.load(f)

    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except: history = {}

    unique_products = {}
    # Priorizar ofertas com maior desconto
    products.sort(key=lambda x: (x.get('custom_discount_pct', 0)), reverse=True)

    for p in products:
        p_id = str(p.get('id', ''))
        if not p_id: continue
        
        p_hash = get_content_hash(p)

        # Se já postado com este ID E este Preço exato, pulamos para evitar SPAM
        # Mas se o preço mudou (hash diferente), permitimos a atualização
        if p_id in history and history[p_id].get('hash') == p_hash:
            continue

        if p_id not in unique_products:
            unique_products[p_id] = p
            history[p_id] = {
                "hash": p_hash,
                "last_update": datetime.now().isoformat()
            }

    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    final_products = list(unique_products.values())
    os.makedirs(os.path.dirname(output_p), exist_ok=True)
    with open(output_p, "w", encoding="utf-8") as f:
        json.dump(final_products, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Deduplicação Inteligente: {len(final_products)} produtos prontos para postagem.")

if __name__ == "__main__":
    process("data/validated_products.json", "data/new_offers.json")
