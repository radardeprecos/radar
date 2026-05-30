import os
import time
from typing import Any, Dict, List, Optional

import requests
from logger import logger

SITE_ID = os.getenv("ML_SITE_ID", "MLB")
ML_CLIENT_ID = os.getenv("ML_CLIENT_ID")
ML_CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
ML_AFILIADO_ID = os.getenv("ML_AFILIADO_ID")
ML_REFRESH_TOKEN = os.getenv("ML_REFRESH_TOKEN")
ML_AUTHORIZATION_CODE = os.getenv("ML_AUTHORIZATION_CODE") or os.getenv("ML_AUTH_CODE")
ML_REDIRECT_URI = os.getenv("ML_REDIRECT_URI")
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
    "User-Agent": "RadarDePrecosBot/2.0 (+https://radardeprecos.github.io/radar/)",
}

SENSITIVE_KEYS = {"client_secret", "access_token", "refresh_token", "code", "authorization"}


def mask_secret(value: Optional[str], visible: int = 4) -> str:
    """Mascara valores sensíveis mantendo apenas um pequeno sufixo para diagnóstico."""
    if value is None:
        return "<ausente>"
    value = str(value)
    if not value:
        return "<vazio>"
    if len(value) <= visible:
        return "*" * len(value)
    return f"{'*' * max(len(value) - visible, 4)}{value[-visible:]}"


def mask_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Retorna uma cópia do payload com secrets mascarados para logs."""
    masked: Dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_KEYS:
            masked[key] = mask_secret(value)
        else:
            masked[key] = value if value not in (None, "") else "<ausente>"
    return masked


def build_oauth_payload(grant_type: str) -> Dict[str, str]:
    """Monta o payload OAuth conforme o grant_type selecionado."""
    payload: Dict[str, str] = {
        "grant_type": grant_type,
        "client_id": ML_CLIENT_ID or "",
        "client_secret": ML_CLIENT_SECRET or "",
    }

    if grant_type == "refresh_token":
        payload["refresh_token"] = ML_REFRESH_TOKEN or ""
    elif grant_type == "authorization_code":
        payload["code"] = ML_AUTHORIZATION_CODE or ""
        if ML_REDIRECT_URI:
            payload["redirect_uri"] = ML_REDIRECT_URI
    elif grant_type == "client_credentials":
        pass
    else:
        logger.warning(
            "grant_type '%s' não reconhecido localmente. A chamada será feita para que a API retorne o erro oficial.",
            grant_type,
        )

    return payload


def validate_oauth_configuration(grant_type: str) -> bool:
    """Valida apenas os campos mínimos por fluxo, sem tratar secrets ausentes como erro do workflow."""
    missing = []
    if not ML_CLIENT_ID:
        missing.append("ML_CLIENT_ID")
    if not ML_CLIENT_SECRET:
        missing.append("ML_CLIENT_SECRET")
    if grant_type == "refresh_token" and not ML_REFRESH_TOKEN:
        missing.append("ML_REFRESH_TOKEN")
    if grant_type == "authorization_code" and not ML_AUTHORIZATION_CODE:
        missing.append("ML_AUTHORIZATION_CODE ou ML_AUTH_CODE")

    if missing:
        logger.error(
            "Configuração OAuth Mercado Livre incompleta para grant_type=%s. Variáveis ausentes: %s",
            grant_type,
            ", ".join(missing),
        )
        return False
    return True


def log_oauth_debug(
    *,
    response: Optional[requests.Response],
    grant_type: str,
    payload: Dict[str, Any],
    error: Optional[BaseException] = None,
) -> None:
    """Registra diagnóstico completo e seguro da chamada oauth/token."""
    status = response.status_code if response is not None else "<sem resposta>"
    response_text = response.text if response is not None else "<sem corpo de resposta>"

    logger.error("Mercado Livre OAuth Debug:")
    logger.error("status=%s", status)
    logger.error("url=%s", OAUTH_TOKEN_URL)
    logger.error("grant_type=%s", grant_type)
    logger.error("redirect_uri=%s", ML_REDIRECT_URI or "<ausente>")
    logger.error("payload=%s", mask_payload(payload))
    logger.error("response=%s", response_text)
    logger.error("corpo do erro retornado pela API=%s", response_text)
    if error is not None:
        logger.error("exception=%s", error)


def post_oauth_token(payload: Dict[str, str], grant_type: str) -> Optional[requests.Response]:
    """Executa a chamada de token com timeout e retry seguro para falhas transitórias."""
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    last_response: Optional[requests.Response] = None
    last_error: Optional[BaseException] = None

    with requests.Session() as session:
        for attempt in range(1, OAUTH_MAX_RETRIES + 1):
            try:
                logger.info(
                    "Solicitando Access Token do Mercado Livre (grant_type=%s, tentativa=%s/%s, timeout=%ss).",
                    grant_type,
                    attempt,
                    OAUTH_MAX_RETRIES,
                    REQUEST_TIMEOUT,
                )
                response = session.post(
                    OAUTH_TOKEN_URL,
                    headers=headers,
                    data=payload,
                    timeout=REQUEST_TIMEOUT,
                )
                last_response = response

                if response.ok:
                    return response

                if response.status_code not in {408, 409, 425, 429, 500, 502, 503, 504}:
                    return response

                logger.warning(
                    "Falha transitória ao obter token Mercado Livre: status=%s tentativa=%s/%s response=%s",
                    response.status_code,
                    attempt,
                    OAUTH_MAX_RETRIES,
                    response.text,
                )
            except requests.RequestException as exc:
                last_error = exc
                logger.warning(
                    "Erro de rede ao obter token Mercado Livre na tentativa %s/%s: %s",
                    attempt,
                    OAUTH_MAX_RETRIES,
                    exc,
                )

            if attempt < OAUTH_MAX_RETRIES:
                time.sleep(OAUTH_RETRY_SLEEP_SECONDS * attempt)

    if last_error is not None and last_response is None:
        log_oauth_debug(response=None, grant_type=grant_type, payload=payload, error=last_error)
    return last_response


def get_access_token() -> Optional[str]:
    """Obtém o access token sem interromper o pipeline caso a API rejeite a autenticação."""
    if ACCESS_TOKEN:
        logger.info("Access Token do Mercado Livre fornecido por variável de ambiente; pulando oauth/token.")
        return ACCESS_TOKEN

    grant_type = ML_GRANT_TYPE
    logger.info("Fluxo OAuth Mercado Livre configurado: grant_type=%s", grant_type)

    if grant_type == "authorization_code":
        logger.warning(
            "authorization_code exige fluxo OAuth completo prévio e código temporário válido. "
            "Para execução recorrente em GitHub Actions, prefira ML_REFRESH_TOKEN com ML_GRANT_TYPE=refresh_token, "
            "ou forneça MERCADOLIBRE_ACCESS_TOKEN/ML_ACCESS_TOKEN quando aplicável."
        )

    if not validate_oauth_configuration(grant_type):
        return None

    payload = build_oauth_payload(grant_type)
    response = post_oauth_token(payload, grant_type)

    if response is None:
        logger.error("Falha ao obter Access Token do Mercado Livre: nenhuma resposta recebida após retries.")
        return None

    if not response.ok:
        log_oauth_debug(response=response, grant_type=grant_type, payload=payload)
        logger.error(
            "Falha ao obter Access Token do Mercado Livre: status=%s. O pipeline continuará sem Authorization para endpoints públicos.",
            response.status_code,
        )
        return None

    try:
        token_data = response.json()
    except ValueError as exc:
        log_oauth_debug(response=response, grant_type=grant_type, payload=payload, error=exc)
        logger.error("Resposta oauth/token não é JSON válido. O pipeline continuará sem Authorization.")
        return None

    token = token_data.get("access_token")
    if not token:
        log_oauth_debug(response=response, grant_type=grant_type, payload=payload)
        logger.error("Resposta oauth/token não contém access_token. O pipeline continuará sem Authorization.")
        return None

    logger.info(
        "Access Token do Mercado Livre obtido com sucesso via grant_type=%s; expires_in=%s; token_type=%s.",
        grant_type,
        token_data.get("expires_in", "<ausente>"),
        token_data.get("token_type", "<ausente>"),
    )
    return token


def configure_auth_header() -> None:
    """Configura o cabeçalho Authorization quando houver token válido, sem encerrar o script em falhas."""
    token = get_access_token()
    if token:
        HEADERS["Authorization"] = f"Bearer {token}"
        logger.info("Token de acesso do Mercado Livre configurado nos cabeçalhos.")
    else:
        logger.warning(
            "Nenhum Access Token Mercado Livre foi configurado. O pipeline continuará usando endpoints públicos; "
            "se a API retornar 403, verifique o diagnóstico OAuth acima."
        )


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


def fetch_by_query(query: str, category_slug: str) -> List[Dict[str, Any]]:
    logger.info(f"Iniciando busca por '{query}' na categoria '{category_slug}'...")
    url = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"
    params = {"q": query, "limit": 50}

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if response.status_code == 403:
            logger.error(
                "Erro 403 ao buscar '%s': acesso proibido. Authorization configurado=%s. response=%s",
                query,
                "Authorization" in HEADERS,
                response.text,
            )
            return []
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        for item in results:
            item["custom_category_slug"] = category_slug

        logger.info(f"Busca por '{query}' retornou {len(results)} produtos.")
        return results
    except requests.RequestException as exc:
        logger.error("Falha HTTP ao buscar '%s': %s", query, exc)
        return []
    except ValueError as exc:
        logger.error("Falha ao decodificar JSON da busca '%s': %s", query, exc)
        return []
    except Exception as exc:
        logger.error("Falha inesperada ao buscar '%s': %s", query, exc)
        return []


def fetch_all_products() -> List[Dict[str, Any]]:
    configure_auth_header()
    all_products = []
    for cat_slug, queries in CATEGORIES_QUERIES.items():
        for query in queries:
            products = fetch_by_query(query, cat_slug)
            all_products.extend(products)
            time.sleep(1.5)
    logger.info(f"Total de produtos brutos buscados: {len(all_products)}")
    return all_products


if __name__ == "__main__":
    import json

    products = fetch_all_products()
    os.makedirs("data", exist_ok=True)
    with open("data/raw_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    logger.info("Produtos brutos salvos em data/raw_products.json")
