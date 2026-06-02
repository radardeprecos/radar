import json
import os
from datetime import datetime

METRICS_FILE = "data/historical_metrics.json"

def collect_metrics():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Carregar métricas existentes
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {"daily": {}, "executions": []}
    
    # Dados atuais do sistema
    db_path = "data/database/all_products.json"
    total_products = 0
    active_products = 0
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
            total_products = len(db)
            active_products = len([p for p in db if p.get("status") == "active"])
            
    total_urls = 0
    xml_files = [f for f in os.listdir(".") if f.startswith("sitemap") and f.endswith(".xml")]
    import re
    for xml in xml_files:
        try:
            with open(xml, "r", encoding="utf-8") as f:
                total_urls += len(re.findall(r"<loc>", f.read()))
        except: continue

    # Registrar execução
    status = "Success"
    if os.path.exists("logs/execution.log"):
        last_log = os.popen("tail -n 10 logs/execution.log").read()
        if "❌" in last_log or "ERROR" in last_log:
            status = "Failure"
            
    execution_entry = {
        "timestamp": timestamp,
        "status": status,
        "products_active": active_products,
        "urls_sitemap": total_urls
    }
    
    history["executions"].append(execution_entry)
    # Manter apenas as últimas 50 execuções
    history["executions"] = history["executions"][-50:]
    
    # Atualizar dados diários
    if today_str not in history["daily"]:
        history["daily"][today_str] = {
            "first_run": timestamp,
            "last_run": timestamp,
            "runs": 0,
            "successes": 0,
            "failures": 0,
            "start_products": active_products,
            "end_products": active_products,
            "start_urls": total_urls,
            "end_urls": total_urls
        }
    
    day_data = history["daily"][today_str]
    day_data["last_run"] = timestamp
    day_data["runs"] += 1
    if status == "Success":
        day_data["successes"] += 1
    else:
        day_data["failures"] += 1
    day_data["end_products"] = active_products
    day_data["end_urls"] = total_urls
    
    # Salvar
    os.makedirs("data", exist_ok=True)
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    collect_metrics()
