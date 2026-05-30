import os
import time
import json
from typing import Any, Dict, List, Optional

import requests
from logger import logger

SITE_ID = os.getenv("ML_SITE_ID", "MLB")
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ML_AFILIADO_ID = os.getenv("ML_AFILIADO_ID")
ML_GRANT_TYPE = os.getenv("ML_GRANT_TYPE", "client_credentials").strip() or "client_credentials"
OAUTH_TOKEN_URL = os.getenv("ML_OAUTH_TOKEN_URL", "https://api.mercadolibre.com/oauth/token")
REQUEST_TIMEOUT = int(os.getenv("ML_REQUEST_TIMEOUT", "20"))
OAUTH_MAX_RETRIES = int(os.getenv("ML_OAUTH_MAX_RETRIES", "3"))
OAUTH_RETRY_SLEEP_SECONDS = float(os.getenv("ML_OAUTH_RETRY_SLEEP_SECONDS", "2"))

ACCESS_TOKEN = (
    os.getenv("MERCADOLIBRE_ACCESS_TOKEN")
    or os.getenv("ML_ACCESS_TOKEN")
    or os.getenv("ML_API_ACCESS_TOKEN")
)

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

SENSITIVE_KEYS = {"client_secret", "access_token", "refresh_token", "code", "authorization"}


def mask_secret(value: Optional[str], visible: int = 4) -> str:
    if value is None:
        return "<ausente>"
    value = str(value)
    if not value:
        return "<vazio>"
    if len(value) <= visible:
        return "*" * len(value)
    return f"{'*' * max(len(value) - visible, 4)}{value[-visible:]}"


def mask_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    masked: Dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_KEYS:
            masked[key] = mask_secret(value)
        else:
            masked[key] = value if value not in (None, "") else "<ausente>"
    return masked


def get_access_token() -> Optional[str]:
    if ACCESS_TOKEN:
        logger.info("Access Token do Mercado Livre fornecido por variável de ambiente.")
        return ACCESS_TOKEN

    if not ML_CLIENT_ID or not ML_CLIENT_SECRET:
        logger.warning("Credenciais ML_CLIENT_ID/SECRET ausentes. Tentando acesso público.")
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
        
        logger.error(f"Erro ao obter token: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Falha na conexão OAuth: {e}")
    
    return None


def normalize_product(item: Dict[str, Any], category_slug: str) -> Dict[str, Any]:
    """Normaliza o item da API do ML para o esquema esperado pelos scripts de build."""
    # O ML retorna 'title', mas o build espera 'name'
    # O ML retorna 'original_price', mas o build espera 'originalPrice'
    price = item.get("price", 0.0)
    original_price = item.get("original_price") or price
    
    return {
        "id": item.get("id", ""),
        "name": item.get("title", "Produto sem título"),
        "title": item.get("title", "Produto sem título"), # Manter ambos por segurança
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
    logger.info(f"Buscando '{query}' em '{category_slug}'...")
    url = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"
    params = {"q": query, "limit": 50}
    
    current_headers = HEADERS.copy()
    if token:
        current_headers["Authorization"] = f"Bearer {token}"
        logger.info("Usando autenticação Bearer.")
    else:
        logger.info("Usando acesso público (sem token).")

    try:
        logger.info(f"Request GET: {url} | Params: {params}")
        response = requests.get(url, params=params, headers=current_headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 403:
            logger.error(f"Erro 403 (Forbidden) na busca. Response: {response.text}")
            # Se falhou com token, tenta sem token como fallback imediato
            if token:
                logger.info("Tentando novamente sem token...")
                return fetch_by_query(query, category_slug, token=None)
            return []
            
        response.raise_for_status()
        results = response.json().get("results", [])
        
        normalized = [normalize_product(item, category_slug) for item in results]
        logger.info(f"Encontrados {len(normalized)} produtos para '{query}'.")
        return normalized
    except Exception as e:
        logger.error(f"Falha ao buscar '{query}': {e}")
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
            time.sleep(1.0) # Rate limit friendly
            
    logger.info(f"Total coletado: {len(all_products)} produtos.")
    return all_products


if __name__ == "__main__":
    products = fetch_all_products()
    os.makedirs("data", exist_ok=True)
    with open("data/raw_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    logger.info("Salvo em data/raw_products.json")
