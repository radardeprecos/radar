import time
import subprocess
import sys
import os
from datetime import datetime

# Configurações
CHECK_INTERVAL = 3600  # Rodar a cada 1 hora (ideal para AdSense e não sobrecarregar)

def run_master():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Iniciando ciclo do mestre...")
    try:
        # Chama o robot_resilience.py que já criamos
        subprocess.run([sys.executable, "scripts/robot_resilience.py"], check=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Ciclo concluído com sucesso.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Erro no ciclo: {e}")

def main():
    print("🚀 ROBÔ RADAR DE PREÇOS ATIVADO (MODO 24/7)")
    print(f"Intervalo de verificação: {CHECK_INTERVAL/60} minutos")
    
    # Muda para a raiz do repositório
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    while True:
        run_master()
        print(f"😴 Aguardando {CHECK_INTERVAL/60} minutos para o próximo ciclo...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
