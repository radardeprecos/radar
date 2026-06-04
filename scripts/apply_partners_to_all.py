import os

repos = [
    '/home/ubuntu/comparapreco.github.io',
    '/home/ubuntu/comprerapido.github.io',
    '/home/ubuntu/radar',
    '/home/ubuntu/superninjas.github.io',
    '/home/ubuntu/granahoje.github.io',
    '/home/ubuntu/casino-radar.github.io'
]

partners_html = """
<!-- Seção de Parceiros - Otimização AdSense -->
<section class="partners-section" style="background: #f9f9f9; padding: 40px 0; border-top: 1px solid #eee; margin-top: 50px; font-family: sans-serif; clear: both;">
    <div style="max-width: 1200px; margin: 0 auto; padding: 0 20px;">
        <h4 style="text-align: center; margin-bottom: 30px; color: #666; font-size: 1.2rem; font-weight: 700;">Nossa Rede de Parceiros</h4>
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; text-align: center;">
            <a href="https://comparapreco.github.io" target="_blank" style="text-decoration: none; color: #333; font-weight: 600; padding: 10px; border: 1px solid #ddd; border-radius: 5px; min-width: 150px;">Compara Preço</a>
            <a href="https://comprerapido.github.io" target="_blank" style="text-decoration: none; color: #333; font-weight: 600; padding: 10px; border: 1px solid #ddd; border-radius: 5px; min-width: 150px;">Compre Rápido</a>
            <a href="https://radardeprecos.github.io/radar/" target="_blank" style="text-decoration: none; color: #333; font-weight: 600; padding: 10px; border: 1px solid #ddd; border-radius: 5px; min-width: 150px;">Radar de Preços</a>
            <a href="https://superninjas.github.io" target="_blank" style="text-decoration: none; color: #333; font-weight: 600; padding: 10px; border: 1px solid #ddd; border-radius: 5px; min-width: 150px;">Super Ninjas</a>
            <a href="https://granahoje.github.io" target="_blank" style="text-decoration: none; color: #333; font-weight: 600; padding: 10px; border: 1px solid #ddd; border-radius: 5px; min-width: 150px;">Grana Hoje</a>
            <a href="https://casino-radar.github.io" target="_blank" style="text-decoration: none; color: #333; font-weight: 600; padding: 10px; border: 1px solid #ddd; border-radius: 5px; min-width: 150px;">Casino Radar</a>
        </div>
        <div style="text-align: center; margin-top: 30px; font-size: 0.8rem; color: #999; border-top: 1px solid #eee; padding-top: 20px;">
            <p>Sites parceiros verificados para transparência e conformidade com as diretrizes do Google AdSense.</p>
        </div>
    </div>
</section>
"""

def apply_to_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        content = "".join(lines)
        if 'partners-section' in content:
            return False
            
        new_lines = []
        applied = False
        for line in lines:
            if '</body>' in line and not applied:
                new_lines.append(partners_html + '\n')
                new_lines.append(line)
                applied = True
            else:
                new_lines.append(line)
        
        if applied:
            with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.writelines(new_lines)
            return True
    except:
        pass
    return False

for repo in repos:
    if not os.path.exists(repo):
        continue
    print(f"Repo: {repo}")
    count = 0
    for root, dirs, files in os.walk(repo):
        if '.git' in root or 'assets' in root:
            continue
        for f in files:
            if f.endswith('.html'):
                if apply_to_file(os.path.join(root, f)):
                    count += 1
    print(f"  {count} arquivos atualizados.")
