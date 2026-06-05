import os
import json
from bs4 import BeautifulSoup

base_dir = '/home/ubuntu/radar_repo'
ml_id = 'radar041-20'
amz_id = 'radar041-20'

def fix_buttons():
    fixed_count = 0
    for root, dirs, files in os.walk(base_dir):
        if any(x in root for x in ['.git', 'scripts', 'assets', 'templates']): continue
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                    
                    # Procurar o JSON-LD para pegar o link de compra
                    json_ld = soup.find('script', type='application/ld+json')
                    if not json_ld: continue
                    
                    data = json.loads(json_ld.string)
                    offer_url = ""
                    if isinstance(data, dict):
                        offers = data.get('offers', {})
                        if isinstance(offers, dict):
                            offer_url = offers.get('url', '')
                        elif isinstance(offers, list) and len(offers) > 0:
                            offer_url = offers[0].get('url', '')
                    
                    if not offer_url: continue
                    
                    # Injetar IDs de afiliados
                    if 'mercadolivre.com' in offer_url and ml_id not in offer_url:
                        connector = '&' if '?' in offer_url else '?'
                        offer_url += f"{connector}matt_tool={ml_id}"
                    elif 'amazon.com.br' in offer_url and amz_id not in offer_url:
                        connector = '&' if '?' in offer_url else '?'
                        offer_url += f"{connector}tag={amz_id}"

                    # Verificar se o botão existe (btn ou btn-ninja)
                    has_btn = soup.find('a', class_=lambda x: x and ('btn' in x or 'btn-ninja' in x))
                    
                    if not has_btn:
                        # Localizar onde inserir o botão
                        price_tag = soup.find('div', class_=lambda x: x and ('price' in x or 'price-tag' in x))
                        if price_tag:
                            btn_html = f'<a href="{offer_url}" class="btn-ninja" style="width: 100%; font-size: 20px; display: block; text-align: center; margin-top: 20px; background: #004aad; color: white; padding: 15px; border-radius: 8px; text-decoration: none; font-weight: bold;" target="_blank">🛒 Ver Alerta de Preço</a>'
                            btn_soup = BeautifulSoup(btn_html, 'html.parser')
                            price_tag.insert_after(btn_soup)
                            
                            with open(path, 'w', encoding='utf-8') as f:
                                f.write(str(soup))
                            fixed_count += 1
                except:
                    continue
    print(f"Botões injetados em {fixed_count} arquivos no Radar.")

if __name__ == "__main__":
    fix_buttons()
