import os
import re
import json
from logger import logger

def audit_site():
    logger.info("Iniciando Auditoria Completa de Erros 404...")
    
    report = {
        "total_links": 0,
        "broken_links": [],
        "fixed_count": 0,
        "checked_files": 0
    }
    
    # 1. Mapear todos os arquivos HTML do site
    html_files = []
    for root, dirs, files in os.walk("."):
        if "noticias/posts" in root or "ofertas" in root or "categorias" in root or "comparar" in root:
            for file in files:
                if file.endswith(".html"):
                    html_files.append(os.path.join(root, file))
    
    # Adicionar index principal
    if os.path.exists("index.html"):
        html_files.append("index.html")

    # 2. Verificar links internos
    for file_path in html_files:
        report["checked_files"] += 1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Regex para encontrar links internos (href e src)
            links = re.findall(r'(?:href|src)="([^"]+)"', content)
            
            for link in links:
                # Ignorar links externos, âncoras e mailto
                if link.startswith(("http", "#", "mailto:", "tel:", "data:")):
                    continue
                
                report["total_links"] += 1
                
                # Normalizar caminho relativo baseado no arquivo atual
                base_dir = os.path.dirname(file_path)
                target_path = os.path.normpath(os.path.join(base_dir, link.split("?")[0].split("#")[0]))
                
                # Se for um diretório, procurar por index.html
                if os.path.isdir(target_path):
                    target_path = os.path.join(target_path, "index.html")

                if not os.path.exists(target_path):
                    report["broken_links"].append({
                        "file": file_path,
                        "link": link,
                        "target": target_path
                    })
        except Exception as e:
            logger.error(f"Erro ao auditar {file_path}: {e}")

    # 3. Correção Automática (Remover links quebrados ou limpar arquivos órfãos)
    # Para simplificar, vamos focar em remover arquivos que apontam para nada ou limpar sitemaps
    logger.info(f"Auditoria finalizada. Encontrados {len(report['broken_links'])} links quebrados.")
    
    # Salvar relatório
    os.makedirs("reports", exist_ok=True)
    with open("reports/audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    return report

if __name__ == "__main__":
    audit_site()
