import json
import os
import requests
from logger import logger

def deep_clean():
    db_path = "data/database/all_products.json"
    if not os.path.exists(db_path):
        logger.error("Banco de dados não encontrado.")
        return

    with open(db_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    total_initial = len(products)
    clean_products = []
    seen_ids = set()

    logger.info(f"Iniciando limpeza profunda em {total_initial} produtos...")

    for p in products:
        p_id = p.get('id')
        p_img = p.get('image') or p.get('thumbnail') or p.get('custom_image_url')
        p_link = p.get('permalink') or p.get('url')

        # 1. Trava de Duplicata
        if p_id in seen_ids:
            continue
        
        # 2. Trava de Imagem (Remover se não tiver imagem ou for placeholder vazio)
        if not p_img or "no-image" in p_img or len(p_img) < 10:
            # logger.info(f"Removendo {p_id} - Sem imagem válida.")
            continue

        # 3. Trava de Link (Básica - presença de URL)
        if not p_link or not p_link.startswith("http"):
            continue

        seen_ids.add(p_id)
        clean_products.append(p)

    # Salvar banco limpo
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(clean_products, f, ensure_ascii=False, indent=2)

    logger.info(f"Limpeza concluída: {total_initial} -> {len(clean_products)} (Removidos: {total_initial - len(clean_products)})")

def cleanup_files():
    """Remove arquivos HTML que não estão no banco de dados limpo."""
    db_path = "data/database/all_products.json"
    with open(db_path, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    valid_ids = {str(p['id']) for p in products}
    
    # Ofertas
    removed_files = 0
    for root, dirs, files in os.walk("ofertas"):
        for file in files:
            if file.endswith(".html"):
                # Extrair ID do final do nome do arquivo (padrão MLB...)
                import re
                match = re.search(r'MLB\d+', file)
                if match:
                    file_id = match.group(0)
                    if file_id not in valid_ids:
                        os.remove(os.path.join(root, file))
                        removed_files += 1
    
    logger.info(f"Sincronização de arquivos: {removed_files} arquivos órfãos removidos.")

if __name__ == "__main__":
    deep_clean()
    cleanup_files()
