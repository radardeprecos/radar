import json
import os
import re
from datetime import datetime
from logger import logger

def generate_dashboard():
    now = datetime.now()
    stats = {
        "last_update": now.strftime("%Y-%m-%d %H:%M:%S"),
        "products": {"total": 0, "active": 0, "expired": 0},
        "pages": {"total": 0, "categories": 0, "blog_posts": 0},
        "sitemaps": {"total_urls": 0, "files": 0},
        "health": "Healthy",
        "duplication_rate": "0%"
    }
    
    # Produtos
    db_path = "data/database/all_products.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
            stats["products"]["total"] = len(db)
            active_list = [p for p in db if p.get("status") == "active"]
            stats["products"]["active"] = len(active_list)
            stats["products"]["expired"] = len([p for p in db if p.get("status") == "expired"])
            
            # Calcular Taxa de Duplicação
            if len(active_list) > 0:
                titles = [p.get('title', '') for p in active_list]
                unique_titles = len(set(titles))
                dup_count = len(titles) - unique_titles
                stats["duplication_rate"] = f"{(dup_count / len(titles)) * 100:.2f}%"

    # Páginas
    stats["pages"]["total"] = len([f for f in os.popen("find ofertas/ -name '*.html'").read().splitlines()])
    stats["pages"]["categories"] = len([f for f in os.popen("find categorias/ -name 'index.html'").read().splitlines()])
    stats["pages"]["blog_posts"] = len([f for f in os.popen("find noticias/posts/ -name '*.html'").read().splitlines()])

    # Sitemaps
    xml_files = [f for f in os.listdir(".") if f.startswith("sitemap") and f.endswith(".xml")]
    stats["sitemaps"]["files"] = len(xml_files)
    total_urls = 0
    for xml in xml_files:
        try:
            with open(xml, "r", encoding="utf-8") as f:
                total_urls += len(re.findall(r"<loc>", f.read()))
        except: continue
    stats["sitemaps"]["total_urls"] = total_urls

    # Health
    if os.path.exists("logs/execution.log"):
        recent_log = os.popen("tail -n 50 logs/execution.log").read()
        if "❌" in recent_log or "ERROR" in recent_log:
            stats["health"] = "Failing"

    # Carregar Histórico
    history = {"daily": {}, "executions": []}
    if os.path.exists("data/historical_metrics.json"):
        with open("data/historical_metrics.json", "r", encoding="utf-8") as f:
            history = json.load(f)

    # Gerar Markdown
    report = f"""# 📊 Dashboard de Observabilidade - Radar de Preços
Atualizado em: {stats['last_update']}

## 🛡️ Status do Sistema
- **Saúde:** {"✅ Healthy" if stats['health'] == "Healthy" else "❌ Failing"}
- **Taxa de Duplicação:** {stats['duplication_rate']} (Meta: < 1%)
- **Sitemaps:** {stats['sitemaps']['total_urls']} URLs em {stats['sitemaps']['files']} arquivos

## 📦 Inventário e Conteúdo
| Métrica | Total |
| :--- | :--- |
| Produtos Ativos | {stats['products']['active']} |
| Produtos Expirados | {stats['products']['expired']} |
| Páginas de Oferta | {stats['pages']['total']} |
| Categorias | {stats['pages']['categories']} |
| Posts no Blog | {stats['pages']['blog_posts']} |

## 🕒 Últimas Execuções
| Timestamp | Status | Produtos | URLs |
| :--- | :--- | :--- | :--- |
"""
    for ex in reversed(history["executions"][-10:]):
        status_icon = "✅" if ex["status"] == "Success" else "❌"
        report += f"| {ex['timestamp']} | {status_icon} {ex['status']} | {ex['products_active']} | {ex['urls_sitemap']} |\n"

    report += "\n## 📅 Resumo Diário (Últimos 7 dias)\n"
    report += "| Data | Runs | Sucessos | Crescimento Prod. | Crescimento URLs |\n"
    report += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    sorted_days = sorted(history["daily"].keys(), reverse=True)
    for day in sorted_days[:7]:
        d = history["daily"][day]
        prod_growth = d['end_products'] - d['start_products']
        url_growth = d['end_urls'] - d['start_urls']
        report += f"| {day} | {d['runs']} | {d['successes']} | {prod_growth:+} | {url_growth:+} |\n"

    os.makedirs("reports", exist_ok=True)
    with open("reports/dashboard.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info("Dashboard de observabilidade atualizado.")

if __name__ == "__main__":
    generate_dashboard()
