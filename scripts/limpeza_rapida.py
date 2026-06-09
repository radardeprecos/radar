import os
import json
import re

db_path = '/home/ubuntu/radar_repo/data/database/all_products.json'
base_dir = '/home/ubuntu/radar_repo'
ml_id = '60566305'
amz_id = '60566305'

def run_quick_clean():
    if not os.path.exists(db_path): return
    with open(db_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    clean_products = []
    for p in products:
        img_url = p.get('image') or p.get('thumbnail') or ''
        # Critério: Remover se for placeholder ou se o nome for suspeito de erro
        if not img_url or 'placeholder' in img_url.lower() or 'error' in img_url.lower() or 'none' in img_url.lower():
            continue
        
        # Injetar IDs de afiliados se faltarem
        url = p.get('custom_affiliate_url', '') or p.get('permalink', '')
        if 'mercadolivre.com' in url and ml_id not in url:
            connector = '&' if '?' in url else '?'
            p['custom_affiliate_url'] = url + f"{connector}matt_tool={ml_id}"
        elif 'amazon.com.br' in url and amz_id not in url:
            connector = '&' if '?' in url else '?'
            p['custom_affiliate_url'] = url + f"{connector}tag={amz_id}"
            
        clean_products.append(p)
    
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(clean_products, f, ensure_ascii=False, indent=2)
    print(f"Limpeza rápida concluída. {len(clean_products)} produtos restantes.")

if __name__ == "__main__":
    run_quick_clean()
