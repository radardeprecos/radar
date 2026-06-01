import json
import os
from datetime import datetime
from logger import logger

HISTORY_FILE = "data/history/price_history.json"

def track_prices():
    db_path = "data/database/all_products.json"
    if not os.path.exists(db_path): return

    with open(db_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = {}

    today = datetime.now().strftime("%Y-%m-%d")
    
    for p in products:
        p_id = str(p.get('id'))
        price = p.get('price', 0)
        
        if p_id not in history:
            history[p_id] = []
        
        # Só adiciona se o último preço for diferente ou se for um novo dia
        if not history[p_id] or history[p_id][-1]['price'] != price:
            history[p_id].append({"date": today, "price": price})
            # Manter apenas os últimos 30 registros
            history[p_id] = history[p_id][-30:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    logger.info(f"Histórico de preços atualizado para {len(products)} produtos.")

if __name__ == "__main__":
    track_prices()
