import os
import json
from logger import logger

def clean_orphans():
    orphan_path = "data/orphan_pages.json"
    if not os.path.exists(orphan_path):
        logger.info("Nenhuma página órfã detectada para limpeza.")
        return
    
    with open(orphan_path, "r", encoding="utf-8") as f:
        orphans = json.load(f)
    
    if not orphans:
        logger.info("Lista de páginas órfãs vazia.")
        return
    
    logger.info(f"Removendo {len(orphans)} páginas órfãs do disco...")
    removed = 0
    for file_path in orphans:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed += 1
            except Exception as e:
                logger.error(f"Erro ao remover {file_path}: {e}")
    
    logger.info(f"Limpeza concluída: {removed} arquivos removidos.")
    
    # Limpar o arquivo de órfãos após a remoção
    with open(orphan_path, "w", encoding="utf-8") as f:
        json.dump([], f)

if __name__ == "__main__":
    clean_orphans()
