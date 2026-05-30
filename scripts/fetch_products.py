import os
import time
import json
from typing import Any, Dict, List, Optional

import requests
from logger import logger

SITE_ID = os.getenv("ML_SITE_ID", "MLB")
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ML_GRANT_TYPE = os.getenv("ML_GRANT_TYPE", "client_credentials").strip() or "client_credentials"
OAUTH_TOKEN_URL = os.getenv("ML_OAUTH_TOKEN_URL", "https://api.mercadolibre.com/oauth/token")
REQUEST_TIMEOUT = int(os.getenv("ML_REQUEST_TIMEOUT", "20"))

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_access_token() -> Optional[str]:
    token = os.getenv("MERCADOLIBRE_ACCESS_TOKEN") or os.getenv("ML_ACCESS_TOKEN") or os.getenv("ML_API_ACCESS_TOKEN")
    if token:
        logger.info("Usando Access Token fornecido via ambiente.")
        return token

    if not ML_CLIENT_ID or not ML_CLIENT_SECRET:
        logger.warning("Credenciais ausentes. Tentando acesso público.")
        return None

    payload = {
        "grant_type": ML_GRANT_TYPE,
        "client_id": ML_CLIENT_ID,
        "client_secret": ML_CLIENT_SECRET,
    }

    try:
        logger.info(f"Solicitando Access Token (grant_type={ML_GRANT_TYPE})...")
        response = requests.post(OAUTH_TOKEN_URL, data=payload, timeout=REQUEST_TIMEOUT)
        if response.ok:
            token = response.json().get("access_token")
            logger.info("Access Token obtido com sucesso.")
            return token
        
        logger.error(f"Falha no OAuth: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Erro de conexão no OAuth: {e}")
    
    return None

def normalize_product(item: Dict[str, Any], category_slug: str) -> Dict[str, Any]:
    price = item.get("price", 0.0)
    original_price = item.get("original_price") or price
    
    return {
        "id": item.get("id", ""),
        "name": item.get("title", "Produto sem título"),
        "title": item.get("title", "Produto sem título"),
        "price": float(price),
        "originalPrice": float(original_price),
        "original_price": float(original_price),
        "permalink": item.get("permalink", ""),
        "thumbnail": item.get("thumbnail", ""),
        "shipping": item.get("shipping", {}),
        "seller": item.get("seller", {}),
        "custom_category_slug": category_slug,
        "sold_quantity": item.get("sold_quantity", 0),
        "condition": item.get("condition", ""),
    }

def fetch_by_query(query: str, category_slug: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    # Tentar busca de catálogo se a busca normal falhar ou for proibida
    # O endpoint /sites/{SITE_ID}/search está retornando 403 em muitos ambientes
    endpoints = [
        f"https://api.mercadolibre.com/sites/{SITE_ID}/search",
        f"https://api.mercadolibre.com/sites/{SITE_ID}/domain_discovery/search"
    ]
    
    params = {"q": query, "limit": 50}
    current_headers = HEADERS.copy()
    
    for url in endpoints:
        for use_auth in [True, False] if token else [False]:
            if use_auth:
                current_headers["Authorization"] = f"Bearer {token}"
                mode = "AUTENTICADO"
            else:
                current_headers.pop("Authorization", None)
                mode = "PÚBLICO"
                
            try:
                logger.info(f"Tentativa [{mode}] -> {url}")
                response = requests.get(url, params=params, headers=current_headers, timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    # domain_discovery retorna formato diferente, mas o search normal retorna results
                    if not results and "domain_id" in data:
                        # Se for domain discovery, podemos tentar buscar pelo domain_id
                        domain_id = data.get("domain_id")
                        logger.info(f"Domain descoberto: {domain_id}. Tentando busca por categoria/domínio.")
                        cat_url = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"
                        cat_params = {"domain_id": domain_id, "limit": 50}
                        response = requests.get(cat_url, params=cat_params, headers=current_headers, timeout=REQUEST_TIMEOUT)
                        if response.status_code == 200:
                            results = response.json().get("results", [])

                    if results:
                        normalized = [normalize_product(item, category_slug) for item in results]
                        logger.info(f"Sucesso: {len(normalized)} produtos para '{query}' ({mode}).")
                        return normalized
                
                logger.warning(f"Falha na tentativa [{mode}] em {url}: {response.status_code}")
                if response.status_code == 403:
                    # Se for 403, pula para a próxima tentativa (pública ou próximo endpoint)
                    continue
                    
            except Exception as e:
                logger.error(f"Erro na tentativa [{mode}] em {url}: {e}")
                continue

    logger.error(f"Todas as tentativas de busca para '{query}' falharam.")
    return []

def fetch_all_products() -> List[Dict[str, Any]]:
    token = get_access_token()
    all_products = []
    
    CATEGORIES_QUERIES = {
        "celulares": ["iPhone", "Samsung Galaxy", "Xiaomi Redmi", "Motorola Edge"],
        "informatica": ["Notebook", "SSD 1TB", "Monitor Gamer", "Teclado Mecanico"],
        "tv-e-video": ["Smart TV 50", "Smart TV 4K", "Chromecast", "Projetor"],
        "eletrodomesticos": ["Air Fryer", "Geladeira Frost Free", "Micro-ondas", "Lava e Seca"],
        "games": ["PlayStation 5", "Nintendo Switch", "Xbox Series S", "Controle PS5"],
        "ferramentas": ["Furadeira", "Jogo de Ferramentas", "Parafusadeira", "Serra Circular"],
        "beleza": ["Secador de Cabelo", "Barbeador Eletrico", "Prancha Alisadora", "Perfume Importado"],
        "casa": ["Mesa de Escritorio", "Cadeira Gamer", "Robo Aspirador", "Jogo de Panelas"],
    }

    for cat_slug, queries in CATEGORIES_QUERIES.items():
        for query in queries:
            products = fetch_by_query(query, cat_slug, token)
            all_products.extend(products)
            time.sleep(1.0)
            
    logger.info(f"Processo de coleta finalizado. Total: {len(all_products)} produtos.")
    return all_products

if __name__ == "__main__":
    try:
        products = fetch_all_products()
        os.makedirs("data", exist_ok=True)
        with open("data/raw_products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        logger.info("Resultados salvos em data/raw_products.json")
    except Exception as e:
        logger.error(f"Erro crítico na coleta: {e}")
        os.makedirs("data", exist_ok=True)
        if not os.path.exists("data/raw_products.json"):
            with open("data/raw_products.json", "w") as f:
                json.dump([], f)
