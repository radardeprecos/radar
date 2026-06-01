import os
import glob
from logger import logger

def cleanup_orphans():
    logger.info("Iniciando limpeza de arquivos órfãos e duplicados...")
    
    # 1. Remover posts de blog com timestamps (o novo sistema usa slugs fixos)
    patterns = [
        "noticias/posts/analise-completa-*.html",
        "noticias/posts/radar-ofertas-*.html"
    ]
    
    removed_count = 0
    for pattern in patterns:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                removed_count += 1
            except Exception as e:
                logger.error(f"Erro ao remover {f}: {e}")
                
    logger.info(f"Limpeza concluída. {removed_count} arquivos removidos.")

if __name__ == "__main__":
    cleanup_orphans()
