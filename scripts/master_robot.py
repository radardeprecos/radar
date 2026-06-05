import subprocess
import os
import sys
from datetime import datetime
from logger import logger

def run_script(script_name):
    """Executa um script python e retorna True se tiver sucesso."""
    logger.info(f"🚀 Iniciando: {script_name}")
    try:
        result = subprocess.run([sys.executable, f"scripts/{script_name}"], 
                                capture_output=True, text=True, check=True)
        logger.info(f"✅ Sucesso: {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro em {script_name}: {e.stderr}")
        return False

def main():
    start_time = datetime.now()
    logger.info(f"🤖 INICIANDO CICLO COMPLETO DO ROBÔ - {start_time.strftime('%d/%m/%Y %H:%M:%S')}")

    # Passo 1: Buscar novos produtos/ofertas (Simulado ou Real dependendo do setup)
    # run_script("fetch_products.py") 

    # Passo 2: Gerar novos artigos de blog (Destravado para AdSense)
    run_script("generate_blog_posts.py")

    # Passo 3: Automação Editorial (Gera o arquivo de tendências)
    run_script("editorial_automation.py")

    # Passo 4: Atualizar Sitemaps (Essencial para o Google achar os novos posts)
    run_script("generate_sitemaps.py")

    # Passo 5: Sincronizar com GitHub
    logger.info("📤 Sincronizando com GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        # Verifica se há algo para commitar
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status:
            subprocess.run(["git", "commit", "-m", f"auto: ciclo do robô concluído em {datetime.now().strftime('%d/%m/%Y %H:%M')}"], check=True)
            subprocess.run(["git", "push", "origin", "main", "--force"], check=True)
            logger.info("✅ GitHub atualizado com sucesso!")
        else:
            logger.info("ℹ️ Nenhuma mudança detectada para subir.")
    except Exception as e:
        logger.error(f"❌ Erro na sincronização com GitHub: {e}")

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"🏁 CICLO CONCLUÍDO EM {duration.total_seconds():.2f}s")

if __name__ == "__main__":
    # Garante que estamos na raiz do repo
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
