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
    
    # Configurar usuário se não estiver configurado
    run_command(["git", "config", "user.email", "manus@manus.im"])
    run_command(["git", "config", "user.name", "Manus AI Robot"])
    
    # Tentar limpar o índice se houver travas
    if os.path.exists(".git/index.lock"):
        logger("Removendo trava do índice git...", "WARNING")
        os.remove(".git/index.lock")
        
    # Adicionar mudanças
    success, out = run_command(["git", "add", "."])
    if not success:
        logger(f"Erro no git add: {out}", "ERROR")
        return False
        
    # Verificar se há mudanças
    success, status = run_command(["git", "status", "--porcelain"])
    if not status.strip():
        logger("Nenhuma mudança para commitar.")
        return True
        
    # Commit
    msg = f"auto: ciclo de auto-cura do robô em {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    success, out = run_command(["git", "commit", "-m", msg])
    if not success:
        logger(f"Erro no git commit: {out}", "ERROR")
        return False
        
    # Push com retentativa
    for i in range(3):
        logger(f"Tentativa de push {i+1}/3...")
        success, out = run_command(["git", "push", "origin", "main", "--force"])
        if success:
            logger("Git push realizado com sucesso!")
            return True
        else:
            logger(f"Falha no push: {out}. Aguardando para tentar novamente...", "WARNING")
            time.sleep(10)
            run_command(["git", "pull", "origin", "main", "--rebase"])
            
    return False

def main_cycle():
    logger("Iniciando ciclo de auto-cura e estabilização...")
    
    # Garantir diretórios
    dirs = ["data/database", "data/products", "ofertas", "artigos", "categorias", "guias"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        
    # Executar pipeline essencial
    essential_scripts = [
        "scripts/build_homepage.py",
        "scripts/generate_sitemaps.py"
    ]
    
    for script in essential_scripts:
        if os.path.exists(script):
            success, out = run_command([sys.executable, script])
            if success:
                logger(f"Script {script} executado com sucesso.")
            else:
                logger(f"Falha no script {script}: {out}", "ERROR")
        else:
            logger(f"Script {script} não encontrado!", "WARNING")
            
    # Sincronizar
    safe_git_push()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main_cycle()
