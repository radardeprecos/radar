
import os
import re
from bs4 import BeautifulSoup

def add_img_dimensions_in_html_and_js(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. Processar tags <img> diretas no HTML
    soup = BeautifulSoup(content, 'html.parser')
    for img in soup.find_all('img'):
        if img.get('width') != '120' or img.get('height') != '120':
            img['width'] = '120'
            img['height'] = '120'
            modified = True

        new_style = 'width:100%;height:auto;'
        if img.get('style') != new_style:
            img['style'] = new_style
            modified = True
    
    if modified:
        content = str(soup)

    # 2. Processar tags <img> dentro de template literals JavaScript
    # Regex para encontrar template literals que contêm <img> tags
    # Isso é uma simplificação e pode não cobrir todos os casos complexos de JS
    template_literal_pattern = re.compile(r'`([^`]*<img[^>]*>[^`]*)`')

    def replace_img_in_template_literal(match):
        nonlocal modified
        literal_content = match.group(1)
        temp_soup = BeautifulSoup(literal_content, 'html.parser')
        temp_modified = False
        for img in temp_soup.find_all('img'):
            if img.get('width') != '120' or img.get('height') != '120':
                img['width'] = '120'
                img['height'] = '120'
                temp_modified = True
            
            new_style = 'width:100%;height:auto;'
            if img.get('style') != new_style:
                img['style'] = new_style
                temp_modified = True
        
        if temp_modified:
            modified = True
            return f'`{str(temp_soup)}`'
        return match.group(0)

    new_content = template_literal_pattern.sub(replace_img_in_template_literal, content)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ Imagens em {file_path} atualizadas.")
    else:
        print(f"- Nenhuma alteração necessária em {file_path}.")

if __name__ == '__main__':
    with open('/home/ubuntu/radar/html_files_to_correct.txt', 'r') as f:
        files = f.read().splitlines()

    for file in files:
        add_img_dimensions_in_html_and_js(file)
