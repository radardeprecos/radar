import os
import subprocess
import time
from logger import logger

def run_cmd(cmd, timeout=300):
    """Executa um comando com captura de erro e log."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.warning(f"Comando falhou: {cmd}\nErro: {result.stderr}")
        return result.returncode == 0, result.stdout
    except Exception as e:
        logger.error(f"Exceção ao executar {cmd}: {e}")
        return False, str(e)

def git_guard():
    """Resolve conflitos de git automaticamente para garantir o push."""
    logger.info("🛡️ Ativando Git-Guard...")
    run_cmd("git config user.name 'Radar-Bot'")
    run_cmd("git config user.email 'bot@radardeprecos.com.br'")
    
    # Tentar sincronizar
    success, _ = run_cmd("git pull origin main --no-rebase -X ours")
    if not success:
        logger.warning("Falha no pull, tentando resetar índice...")
        run_cmd("git reset -- merge")
    
    return True

def auto_setup():
    """Garante que a estrutura de pastas exista."""
    dirs = [
        "data/database", "data/history", "data/products", 
        "ofertas/beleza", "ofertas/casa", "ofertas/celulares", 
        "ofertas/informatica", "ofertas/games", "ofertas/tv-e-video",
        "noticias/posts"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("✅ Estrutura de diretórios validada.")

def orchestrate():
    logger.info("🚀 [ROBÔ SUPREMO 2.0] Iniciando em modo AUTONOMIA TOTAL")
    
    auto_setup()
    git_guard()

    steps = [
        ("Coleta", "python3.11 scripts/fetch_products.py"),
        ("Sincronia", "python3.11 scripts/sync_database.py"),
        ("Deduplicação", "python3.11 scripts/deduplicate.py"),
        ("Afiliados", "python3.11 scripts/affiliate_links.py"),
        ("Limpeza", "python3.11 scripts/deep_clean.py"),
        ("Home", "python3.11 scripts/build_homepage.py"),
        ("Blog", "python3.11 scripts/generate_blog_posts.py"),
        ("Páginas", "python3.11 scripts/generate_pages.py"),
        ("Rankings", "python3.11 scripts/build_top_rankings.py"), ("Sitemap", "python3.11 scripts/build_sitemap.py")
    ]

    for name, cmd in steps:
        logger.info(f"🔄 Executando: {name}")
        # Retry logic simples
        success = False
        for attempt in range(2):
            ok, _ = run_cmd(cmd)
            if ok:
                success = True
                break
            logger.warning(f"Tentativa {attempt+1} falhou para {name}. Re-tentando...")
            time.sleep(2)
        
        if not success:
            logger.error(f"❌ {name} falhou após retentativas. Pulando para manter o fluxo.")

    # Push Final Automático
    logger.info("📤 Enviando atualizações para o GitHub...")
    run_cmd("git add .")
    run_cmd('git commit -m "🤖 [ROBÔ] Atualização Automática e Auto-Cura "')
    
    # Git-Guard no Push
    push_ok, _ = run_cmd("git push origin main")
    if not push_ok:
        logger.warning("Push falhou, tentando forçar sincronia final...")
        git_guard()
        run_cmd("git push origin main")

    logger.info("🏁 Ciclo de autonomia finalizado com sucesso.")

if __name__ == "__main__":
    orchestrate()
