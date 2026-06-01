import json
import os
from logger import logger

AFFILIATE_ID = "vendas0nline"

def apply_affiliate_links():
    db_path = "data/database/all_products.json"
    if not os.path.exists(db_path):
        return

    with open(db_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    logger.info(f"Aplicando link de afiliado '{AFFILIATE_ID}' em {len(products)} produtos...")
    
    updated_count = 0
    ml_only_products = []

    for p in products:
        url = p.get('permalink') or p.get('url', '')
        
        # FILTRO: Apenas Mercado Livre
        if "mercadolivre.com.br" in url or "mlstatic.com" in url:
            # Injetar o parâmetro de afiliado se não existir ou estiver diferente
            if "matt_tool=" not in url:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}matt_tool={AFFILIATE_ID}"
            else:
                # Substituir matt_tool existente
                import re
                url = re.sub(r'matt_tool=[^&]+', f'matt_tool={AFFILIATE_ID}', url)
            
            p['custom_affiliate_url'] = url
            p['permalink'] = url
            ml_only_products.append(p)
            updated_count += 1
        else:
            # logger.info(f"Removendo produto de outra loja: {url}")
            continue

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(ml_only_products, f, ensure_ascii=False, indent=2)

    logger.info(f"Sucesso: {updated_count} links de afiliado atualizados. Outras lojas removidas.")

if __name__ == "__main__":
    apply_affiliate_links()
