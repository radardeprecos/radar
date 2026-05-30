import os
import sys
import time
import requests
from typing import List, Dict, Any
from logger import logger

SITE_ID = os.getenv("ML_SITE_ID", "MLB")
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ACCESS_TOKEN = (
    os.getenv("MERCADOLIBRE_ACCESS_TOKEN")
    or os.getenv("ML_ACCESS_TOKEN")
    or os.getenv("ML_API_ACCESS_TOKEN")
)

def get_access_token() -> str:
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    if not ML_CLIENT_ID or not ML_CLIENT_SECRET:
        logger.error("ML_CLIENT_ID ou ML_CLIENT_SECRET não configurados. Não é possível obter Access Token.")
        raise ValueError("Credenciais de cliente do Mercado Livre ausentes.")

    token_url = "https://api.mercadolibre.com/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": ML_CLIENT_ID,
        "client_secret": ML_CLIENT_SECRET,
    }
    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=20)
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Erro detalhado da API ML: {e.response.text}")
        logger.error(f"Falha ao obter Access Token do Mercado Livre: {e}")
        raise

# Obter o token de acesso no início do script
try:
    ML_AUTH_TOKEN = get_access_token()
    HEADERS["Authorization"] = f"Bearer {ML_AUTH_TOKEN}"
    logger.info("Token de acesso do Mercado Livre obtido e configurado nos cabeçalhos.")
except ValueError:
    logger.warning("Não foi possível obter o Access Token. As requisições à API podem falhar.")
except Exception as e:
    logger.error(f"Erro crítico ao configurar o token de acesso: {e}")
    sys.exit(1)



CATEGORIES_QUERIES = {
    "celulares": ["iPhone", "Samsung Galaxy", "Xiaomi Redmi", "Motorola Edge"],
    "informatica": ["Notebook", "SSD 1TB", "Monitor Gamer", "Teclado Mecanico"],
    "tv-e-video": ["Smart TV 50", "Smart TV 4K", "Chromecast", "Projetor"],
    "eletrodomesticos": ["Air Fryer", "Geladeira Frost Free", "Micro-ondas", "Lava e Seca"],
    "games": ["PlayStation 5", "Nintendo Switch", "Xbox Series S", "Controle PS5"],
    "ferramentas": ["Furadeira", "Jogo de Ferramentas", "Parafusadeira", "Serra Circular"],
    "beleza": ["Secador de Cabelo", "Barbeador Eletrico", "Prancha Alisadora", "Perfume Importado"],
    "casa": ["Mesa de Escritorio", "Cadeira Gamer", "Robo Aspirador", "Jogo de Panelas"]
}

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "RadarDePrecosBot/2.0 (+https://radardeprecos.github.io/radar/)"
}

if ACCESS_TOKEN:
    HEADERS["Authorization"] = f"Bearer {ACCESS_TOKEN}"
    logger.info("Token de acesso configurado e adicionado aos cabeçalhos.")
else:
    logger.warning("Nenhum Token de acesso configurado! A API pode retornar 403.")

def fetch_by_query(query: str, category_slug: str) -> List[Dict[str, Any]]:
    logger.info(f"Iniciando busca por '{query}' na categoria '{category_slug}'...")
    url = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"
    params = {
        "q": query,
        "limit": 50
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if response.status_code == 403:
            logger.error("Erro 403: Acesso Proibido. A API exige Token de Acesso válido.")
            return []
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        
        # Inserir a categoria em cada item
        for item in results:
            item["custom_category_slug"] = category_slug
            
        logger.info(f"Busca por '{query}' retornou {len(results)} produtos.")
        return results
    except Exception as e:
        logger.error(f"Falha ao buscar '{query}': {e}")
        return []

def fetch_all_products() -> List[Dict[str, Any]]:
    all_products = []
    for cat_slug, queries in CATEGORIES_QUERIES.items():
        for query in queries:
            products = fetch_by_query(query, cat_slug)
            all_products.extend(products)
            time.sleep(1.5)  # Respeitar rate limit
    logger.info(f"Total de produtos brutos buscados: {len(all_products)}")
    return all_products

if __name__ == "__main__":
    import json
    products = fetch_all_products()
    os.makedirs("data", exist_ok=True)
    with open("data/raw_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    logger.info("Produtos brutos salvos em data/raw_products.json")
