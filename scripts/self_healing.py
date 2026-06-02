import os
import sys
import json
import subprocess
import time
from logger import logger

# Configurações de Resiliência
DEFAULT_TIMEOUT = 300 # 5 minutos por script
MAX_RETRIES = 1

def run_script_protected(script, timeout=DEFAULT_TIMEOUT):
    """Executa um script com proteção de tempo e isolamento."""
    try:
        logger.info(f"🚀 Iniciando {script}...")
        result = subprocess.run(
            [sys.executable, f"scripts/{script}"],
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr or result.stdout
            
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT: O script {script} excedeu o limite de {timeout}s."
    except Exception as e:
        return False, f"CRITICAL ERROR: {str(e)}"

def run_pipeline():
    """Pipeline imparável com isolamento de falhas."""
    scripts = [
        "fetch_products.py", "score_products.py", "affiliate_links.py",
        "validate_products.py", "deduplicate.py", "deep_clean_duplicates.py", 
        "audit_orphan_pages.py", "clean_orphans.py", "sync_database.py",
        "generate_blog_posts.py", "generate_pages.py", "build_categories.py", 
        "generate_comparisons.py", "build_homepage.py", "generate_sitemaps.py", 
        "generate_feeds.py", "health_monitor.py", "metrics_collector.py", 
        "revenue_tracker.py", "dashboard.py"
    ]
    
    for script in scripts:
        success, last_error = run_script_protected(script)
        if not success:
            logger.warning(f"⚠️ {script} falhou. Erro: {last_error[:100]}...")
            # Tentativa de retry simples
            success, last_error = run_script_protected(script)
            if not success:
                logger.error(f"❌ {script} falhou definitivamente. Pulando...")
                
    return True

if __name__ == "__main__":
    logger.info("=== INICIANDO PIPELINE FASE 2 ===")
    start_time = time.time()
    run_pipeline()
    duration = time.time() - start_time
    logger.info(f"✅ Pipeline finalizado em {duration:.1f}s!")
