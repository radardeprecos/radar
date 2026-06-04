import os
from datetime import datetime

BASE_URL = "https://radardeprecos.github.io/"

def generate_valid_sitemap():
    print("Iniciando correção do sitemap baseada em arquivos físicos...")
    
    # 1. Coletar arquivos HTML reais
    valid_urls = [
        BASE_URL,
        f"{BASE_URL}noticias/",
        f"{BASE_URL}melhores-ofertas/",
        f"{BASE_URL}sobre/",
        f"{BASE_URL}contato/",
    ]
    
    # Ofertas
    ofertas_count = 0
    if os.path.exists("ofertas"):
        for root, dirs, files in os.walk("ofertas"):
            for file in files:
                if file.endswith(".html"):
                    rel_path = os.path.relpath(os.path.join(root, file), ".")
                    url = f"{BASE_URL}{rel_path}"
                    valid_urls.append(url)
                    ofertas_count += 1
                    
    # Categorias
    cat_count = 0
    if os.path.exists("categorias"):
        for root, dirs, files in os.walk("categorias"):
            for file in files:
                if file.endswith("index.html"):
                    rel_path = os.path.relpath(os.path.join(root, file), ".")
                    url = f"{BASE_URL}{rel_path}"
                    valid_urls.append(url)
                    cat_count += 1

    # 2. Gerar XML Único e Robusto (Sitemap.xml)
    now = datetime.now().strftime("%Y-%m-%d")
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', 
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    
    for url in sorted(list(set(valid_urls))):
        xml.append('  <url>')
        xml.append(f'    <loc>{url}</loc>')
        xml.append(f'    <lastmod>{now}</lastmod>')
        xml.append('    <changefreq>daily</changefreq>')
        xml.append('    <priority>0.7</priority>')
        xml.append('  </url>')
    
    xml.append('</urlset>')
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml))
        
    print(f"Sucesso! Sitemap.xml gerado com {len(valid_urls)} URLs válidas.")
    print(f"- Ofertas encontradas: {ofertas_count}")
    print(f"- Categorias encontradas: {cat_count}")

if __name__ == "__main__":
    generate_valid_sitemap()
