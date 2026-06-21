import os
import subprocess
import time
from datetime import datetime
import sys

def logger(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def run_command(cmd, timeout=600):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout Expired"
    except Exception as e:
        return False, str(e)

def safe_git_push():
    logger("Iniciando sincronização Git resiliente...")
    run_command(["git", "config", "user.email", "manus@manus.im"])
    run_command(["git", "config", "user.name", "Manus AI Robot"])
    
    if os.path.exists(".git/index.lock"):
        os.remove(".git/index.lock")
        
    run_command(["git", "add", "."])
    success, status = run_command(["git", "status", "--porcelain"])
    if not status.strip():
        logger("Nenhuma mudança para commitar.")
        return True
        
    msg = f"auto: ciclo de auto-cura e conteúdo em {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run_command(["git", "commit", "-m", msg])
    
    for i in range(3):
        logger(f"Tentativa de push {i+1}/3...")
        success, out = run_command(["git", "push", "origin", "main", "--force"])
        if success:
            logger("Git push realizado com sucesso!")
            return True
        else:
            logger(f"Falha no push: {out}. Tentando rebase...", "WARNING")
            time.sleep(5)
            run_command(["git", "pull", "origin", "main", "--rebase"])
            
    return False

def main_cycle():
    logger("🚀 INICIANDO CICLO DE AUTO-CURA E CONTEÚDO")
    
    # 1. Garantir diretórios
    dirs = ["data/database", "data/products", "ofertas", "artigos", "noticias/posts", "categorias", "guias"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        
    # 2. Gerar Conteúdo de Alto Valor (Evita 'Low Value Content' no AdSense)
    logger("Gerando postagens de alto valor...")
    run_command([sys.executable, "scripts/generate_high_value_posts.py"])
    
    # 3. Executar Pipeline de Build
    essential_scripts = [
        "scripts/build_homepage.py",
        "scripts/generate_sitemaps.py"
    ]
    
    for script in essential_scripts:
        if os.path.exists(script):
            success, out = run_command([sys.executable, script])
            if not success:
                logger(f"⚠️ Falha no script {script}: {out}", "WARNING")
    
    # 4. Sincronização Final
    safe_git_push()
    logger("🏁 CICLO FINALIZADO")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main_cycle()
