import os
import json
import requests
from typing import Any, Dict, List
from logger import logger

# Configurações via Environment Variables (GitHub Secrets)
ML_CLIENT_ID = os.environ.get("ML_CLIENT_ID")
ML_CLIENT_SECRET = os.environ.get("ML_CLIENT_SECRET")
ML_AFILIADO_ID = os.environ.get("ML_AFILIADO_ID", "vendas0nline")

def get_access_token():
    if not ML_CLIENT_ID or not ML_CLIENT_SECRET:
        logger.error("❌ Erro: ML_CLIENT_ID ou ML_CLIENT_SECRET não configurados nos Secrets do GitHub.")
        return None
    
    try:
        url = "https://api.mercadolibre.com/oauth/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": ML_CLIENT_ID,
            "client_secret": ML_CLIENT_SECRET
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        logger.error(f"❌ Falha na autenticação OAuth2: {e}")
        return None

def fetch_ml_offers(token):
    # Categorias populares: Celulares (MLB1051), Informática (MLB1648), Games (MLB1144), Eletrodomésticos (MLB1182)
    categories = ["MLB1051", "MLB1648", "MLB1144", "MLB1182"]
    all_offers = []
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for cat in categories:
        try:
            url = f"https://api.mercadolibre.com/sites/MLB/search?category={cat}&sort=price_asc&limit=30"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                results = response.json().get("results", [])
                for item in results:
                    price = item.get("price")
                    original = item.get("original_price")
                    
                    discount = 0
                    if original and price and original > price:
                        discount = int(((original - price) / original) * 100)
                    
                    all_offers.append({
                        "id": item.get("id"),
                        "name": item.get("title"),
                        "title": item.get("title"),
                        "price": price,
                        "original_price": original,
                        "permalink": item.get("permalink"),
                        "image": item.get("thumbnail").replace("-I.jpg", "-O.jpg"),
                        "thumbnail": item.get("thumbnail"),
                        "custom_category_slug": cat,
                        "custom_discount_pct": discount,
                        "data_atualizacao": item.get("stop_time")
                    })
            logger.info(f"Capturadas {len(results)} ofertas para categoria {cat}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao buscar categoria {cat}: {e}")
            
    return all_offers

def main():
    raw_path = "data/raw_products.json"
    
    token = get_access_token()
    
    if not token:
        logger.warning("🚨 Abortando captura por falta de credenciais. Mantendo ofertas atuais como fallback.")
        return

    new_products = fetch_ml_offers(token)
    
    if not new_products:
        logger.warning("🚨 Nenhuma oferta nova capturada pela API. Mantendo banco de dados atual.")
        return

    os.makedirs("data", exist_ok=True)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(new_products, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Sucesso: {len(new_products)} ofertas reais salvas em {raw_path}")

if __name__ == "__main__":
    main()
