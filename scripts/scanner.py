import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

SITE_ID = os.getenv("ML_SITE_ID", "MLB")
AFILIADO_ID = os.getenv("ML_AFILIADO_ID", "vendas0nline")
MIN_DISCOUNT = int(os.getenv("MIN_DISCOUNT", "15"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
ACCESS_TOKEN = (
    os.getenv("MERCADOLIBRE_ACCESS_TOKEN")
    or os.getenv("ML_ACCESS_TOKEN")
    or os.getenv("ML_API_ACCESS_TOKEN")
)

CATEGORIES = {
    "Celulares": ["iPhone 15", "Galaxy S24", "Xiaomi"],
    "Games": ["PS5", "Nintendo Switch", "Xbox"],
    "Informática": ["Notebook", "SSD", "Monitor"],
    "Eletrodomésticos": ["Air Fryer", "Geladeira", "Micro-ondas"],
}

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "RadarDePrecosBot/1.0 (+https://radardeprecos.github.io/radar/)",
}

if ACCESS_TOKEN:
    HEADERS["Authorization"] = f"Bearer {ACCESS_TOKEN}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_image(url: Optional[str]) -> str:
    if not url:
        return ""
    return url.replace("-I.jpg", "-O.jpg")


def affiliate_url(item_id: str, permalink: Optional[str] = None) -> str:
    """Gera link de saída. Mantém o link social configurado no projeto.

    Caso o formato social deixe de funcionar, o permalink original fica disponível
    no JSON como campo auxiliar para auditoria futura.
    """
    return f"https://www.mercadolivre.com.br/social/{AFILIADO_ID}?item={item_id}"


def parse_item(item: Dict[str, Any], category: str) -> Optional[Dict[str, Any]]:
    price = item.get("price")
    original_price = item.get("original_price")
    item_id = item.get("id")
    title = item.get("title")

    if not item_id or not title or not isinstance(price, (int, float)):
        return None

    if not isinstance(original_price, (int, float)) or original_price <= price:
        return None

    discount = int(round(((original_price - price) / original_price) * 100))
    if discount < MIN_DISCOUNT:
        return None

    permalink = item.get("permalink")
    return {
        "id": item_id,
        "name": title,
        "price": round(float(price), 2),
        "originalPrice": round(float(original_price), 2),
        "discount": discount,
        "image": normalize_image(item.get("thumbnail")),
        "url": affiliate_url(item_id, permalink),
        "permalink": permalink,
        "category": category,
    }


def search(query: str, category: str) -> List[Dict[str, Any]]:
    print(f"Buscando {query}...")
    url = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"
    params = {"q": query, "limit": 50}
    response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)

    if response.status_code == 403:
        raise RuntimeError(
            "A API do Mercado Livre retornou 403 Forbidden para o endpoint "
            f"{url}. Configure um token válido em MERCADOLIBRE_ACCESS_TOKEN/ML_ACCESS_TOKEN "
            "e confirme no DevCenter se a aplicação tem permissão para esse recurso."
        )

    if response.status_code == 401:
        raise RuntimeError(
            "A API do Mercado Livre retornou 401 Unauthorized. O token configurado está ausente, "
            "expirado ou inválido."
        )

    response.raise_for_status()
    payload = response.json()
    return [
        parsed
        for item in payload.get("results", [])
        if (parsed := parse_item(item, category)) is not None
    ]


def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> int:
    started_at = now_iso()
    all_items: List[Dict[str, Any]] = []
    errors: List[str] = []

    for category, queries in CATEGORIES.items():
        for query in queries:
            try:
                all_items.extend(search(query, category))
            except Exception as exc:  # imprime todos os erros para facilitar debug no Actions
                message = f"{category}/{query}: {exc}"
                errors.append(message)
                print(f"ERRO: {message}", file=sys.stderr)
            time.sleep(1)

    all_items.sort(key=lambda item: item["discount"], reverse=True)
    write_json(
        "data/logs/scanner_last_run.json",
        {
            "startedAt": started_at,
            "finishedAt": now_iso(),
            "siteId": SITE_ID,
            "minDiscount": MIN_DISCOUNT,
            "tokenConfigured": bool(ACCESS_TOKEN),
            "offerCount": len(all_items),
            "errors": errors,
        },
    )

    if not all_items:
        print(
            "Nenhuma oferta real foi gerada. O arquivo data/products/offers.json não foi sobrescrito "
            "para evitar publicar produto fictício.",
            file=sys.stderr,
        )
        return 1

    write_json("data/products/offers.json", all_items[:100])
    print(f"Sucesso: {len(all_items)} ofertas reais com link de afiliado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
