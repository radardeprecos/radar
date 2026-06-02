import os
import re
from logger import logger

def fix_links():
    logger.info("Iniciando Correção Inteligente de Links (404)...")
    
    # Mapear arquivos HTML
    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root:
            continue
            
        depth = root.count(os.sep)
        # Se estiver na raiz, prefixo é vazio. Se estiver em subpasta, prefixo é ../
        prefix = "../" * depth if depth > 0 else ""
        
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    new_content = content
                    
                    # 1. Corrigir links de assets que começam com / ou estão sem prefixo correto
                    new_content = re.sub(r'(src|href)="/assets/', f'\\1="{prefix}assets/', new_content)
                    
                    # 2. Corrigir links para index
                    new_content = re.sub(r'href="/(index\.html)?"', f'href="{prefix if prefix else "./"}"', new_content)
                    new_content = re.sub(r'href="/radar/(index\.html)?"', f'href="{prefix if prefix else "./"}"', new_content)
                    
                    # 3. Corrigir links para categorias e ofertas (sempre usar relativo ao root)
                    # Se o link começa com /ofertas ou /categorias, substituir pelo prefixo relativo
                    new_content = re.sub(r'href="/ofertas/', f'href="{prefix}ofertas/', new_content)
                    new_content = re.sub(r'href="/categorias/', f'href="{prefix}categorias/', new_content)
                    new_content = re.sub(r'href="/comparar/', f'href="{prefix}comparar/', new_content)
                    new_content = re.sub(r'href="/noticias/', f'href="{prefix}noticias/', new_content)

                    if new_content != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                except Exception as e:
                    logger.error(f"Erro ao corrigir {file_path}: {e}")

    logger.info("Correção Inteligente finalizada.")

if __name__ == "__main__":
    fix_links()
