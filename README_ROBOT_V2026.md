# 🚀 Guia de Replicação: Motor do Robô Ninja

Este pacote contém a inteligência de automação e SEO que deve ser replicada nos outros projetos. **A monetização está protegida.**

## 📋 Arquivos para Copiar
Copie os seguintes arquivos para a raiz do seu novo projeto:

1. **Scripts de Inteligência** (`/scripts`):
   * `generate_sitemap_dynamic.py` -> Gerador de Sitemap 2026.
   * `self_healing.py` -> Sistema de autocura de links.
   * `navigation_audit.py` -> Auditoria de 404.
2. **Páginas Estruturais**:
   * `404.html`
   * `robots.txt`
   * `sobre.html`, `contato.html`, `privacidade.html` (Editar apenas o nome do site).

## 🛡️ Áreas Protegidas (NÃO MEXER)
**NUNCA** substitua os seguintes arquivos/pastas, pois eles contêm sua monetização:
* `ofertas/` (Seus links de afiliado estão aqui).
* `public_data.json` (Seu banco de produtos).

*Nota: O script `scripts/affiliate_links.py` agora é configurável via variáveis de ambiente para facilitar a troca de IDs sem mexer no código.*

## ⚙️ Configuração de Afiliados
Os scripts agora suportam variáveis de ambiente:
- `ML_AFILIADO_ID`: Seu ID do Mercado Livre (ex: vendas0nline)
- `AMZ_AFILIADO_ID`: Seu ID da Amazon (ex: radar041-20)

## 📤 Publicação Automática
O robô agora faz o `git push` automaticamente ao final do ciclo. Certifique-se de que o servidor tenha permissão de escrita no GitHub.

## 🛠️ Como Aplicar as Melhorias
Após copiar os scripts, execute na ordem:

1. **Limpeza de 404**: `python3 scripts/clean_sitemaps.py`
2. **Visual de Categorias**: `python3 scripts/refactor_categories.py`
3. **Ajuste de Breadcrumbs e Preços**: `python3 scripts/final_html_cleanup.py`
4. **Gerar Sitemap Final**: `python3 scripts/generate_sitemap_dynamic.py`

## 📦 Dependências
Certifique-se de ter instalado:
* `pip install beautifulsoup4 lxml`
