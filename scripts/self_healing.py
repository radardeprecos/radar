import os
import subprocess
import glob
from logger import logger

def run_step(name, command):
    logger.info(f"🚀 Iniciando Etapa: {name}")
    try:
        # shell=True para suportar pipes e redirecionamentos se necessário
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info(f"✅ {name} concluído com sucesso.")
            return True
        else:
            logger.warning(f"⚠️ {name} falhou com código {result.returncode}. Continuando...")
            logger.debug(f"Erro: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro crítico em {name}: {e}. Continuando pipeline...")
        return False

def orchestrate():
    logger.info("🤖 Iniciando Orquestrador Supremo (Modo Fluxo Contínuo)")
    
    # 1. Coleta e Sincronização
    run_step("Fetch Products", "python3.11 scripts/fetch_products.py")
    run_step("Sync Database", "python3.11 scripts/sync_database.py")
    
    # 2. Blindagem e Limpeza (Não bloqueante)
    run_step("Deduplicate", "python3.11 scripts/deduplicate.py")
    run_step("Affiliate Links", "python3.11 scripts/affiliate_links.py")
    run_step("Deep Clean", "python3.11 scripts/deep_clean.py")
    
    # 3. Geração de Conteúdo
    run_step("Build Homepage", "python3.11 scripts/build_homepage.py")
    run_step("Generate Blog", "python3.11 scripts/generate_blog_posts.py")
    run_step("Generate Pages", "python3.11 scripts/generate_pages.py")
    
    # 4. Finalização
    run_step("Build Sitemap", "python3.11 scripts/build_sitemap.py")
    
    logger.info("🏁 Pipeline finalizado. Sistema em estado de Auto-Cura.")

if __name__ == "__main__":
    orchestrate()
