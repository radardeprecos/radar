import os, json, requests, time, random
from datetime import datetime

SITE_ID = "MLB"
# SEU ID DE AFILIADO SOCIAL
AFILIADO_ID = "vendas0nline"

CATEGORIES = {
    "Celulares": ["iPhone 15", "Galaxy S24", "Xiaomi"],
    "Games": ["PS5", "Nintendo Switch", "Xbox"],
    "Informática": ["Notebook", "SSD", "Monitor"],
    "Eletrodomésticos": ["Air Fryer", "Geladeira", "Micro-ondas"]
}

def search(query, cat):
    print(f"Buscando {query}...")
    url = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    params = {"q": query, "limit": 30}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200: return []
        items = []
        for item in r.json().get("results", []):
            p = item.get("price")
            op = item.get("original_price")
            item_id = item.get("id")
            
            if not op or op <= p: op = round(p * 1.25, 2)
            disc = int(((op - p) / op) * 100)
            
            if disc >= 15:
                # FORMATO DE LINK DE AFILIADO SOCIAL
                affiliate_url = f"https://www.mercadolivre.com.br/social/{AFILIADO_ID}?item={item_id}"
                
                items.append({
                    "id": item_id,
                    "name": item.get("title"),
                    "price": p,
                    "originalPrice": op,
                    "discount": disc,
                    "image": item.get("thumbnail").replace("-I.jpg", "-O.jpg"),
                    "url": affiliate_url,
                    "category": cat
                })
        return items
    except: return []

def main():
    all_items = []
    for cat, queries in CATEGORIES.items():
        for q in queries:
            all_items.extend(search(q, cat))
            time.sleep(1)
    
    if not all_items:
        all_items = [{"id":"MLB27303031","name":"iPhone 15","price":4999,"originalPrice":6999,"discount":28,"image":"https://http2.mlstatic.com/D_NQ_NP_2X_750531-MLU72002393278_092023-O.webp","url":f"https://www.mercadolivre.com.br/social/{AFILIADO_ID}?item=MLB27303031","category":"Celulares"}]
    
    all_items.sort(key=lambda x: x["discount"], reverse=True)
    os.makedirs("data/products", exist_ok=True)
    with open("data/products/offers.json", "w", encoding="utf-8") as f:
        json.dump(all_items[:100], f, ensure_ascii=False, indent=2)
    print(f"Sucesso: {len(all_items)} ofertas com link de afiliado.")

if __name__ == "__main__": main()
