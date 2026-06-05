import os
import re

base_dir = '/home/ubuntu/radardeprecos.github.io/radar'
sitemaps = [f for f in os.listdir(base_dir) if f.startswith('sitemap') and f.endswith('.xml')]

def check_url_exists(url):
    # Remover o domínio (https://radardeprecos.github.io/radar/)
    path = url.replace('https://radardeprecos.github.io/radar/', '')
    if not path or path == '/': return True
    
    full_path = os.path.join(base_dir, path.strip('/'))
    
    if os.path.exists(full_path): return True
    if os.path.exists(full_path + '.html'): return True
    if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, 'index.html')): return True
    
    return False

for sm in sitemaps:
    sm_path = os.path.join(base_dir, sm)
    print(f"Limpando {sm}...")
    
    with open(sm_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontrar todos os blocos <url>...</url>
    url_blocks = re.findall(r'<url>.*?</url>', content, re.DOTALL)
    
    valid_blocks = []
    removed_count = 0
    
    for block in url_blocks:
        loc_match = re.search(r'<loc>(.*?)</loc>', block)
        if loc_match:
            url = loc_match.group(1)
            if check_url_exists(url):
                valid_blocks.append(block)
            else:
                removed_count += 1
    
    if removed_count > 0:
        # Reconstruir o sitemap mantendo o cabeçalho e rodapé
        header = content.split('<url>')[0]
        footer = content.split('</url>')[-1]
        new_content = header + "\n".join(valid_blocks) + footer
        
        with open(sm_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Removidos {removed_count} links quebrados de {sm}")
    else:
        print(f"  Nenhum link quebrado em {sm}")
