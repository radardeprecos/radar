# 🥷 Guia de Replicação - Robô Radar Ninja

Este pacote contém o "motor" completo do Radar Ninja, pronto para ser instalado em um novo repositório GitHub Pages.

## 🚀 Como Replicar em 5 Minutos

1.  **Novo Repositório:** Crie um novo repositório no GitHub (ex: `meunovo-site.github.io`).
2.  **Upload:** Suba todos os arquivos deste pacote para o novo repositório.
3.  **Configuração Global:**
    *   Abra os arquivos na pasta `scripts/` e procure por `BASE_URL`.
    *   Altere `https://radardeprecos.github.io/radar/` para a URL do seu novo site.
    *   *Dica:* Use o comando `grep -r "radardeprecos.github.io/radar" .` para encontrar todas as menções.
4.  **GitHub Actions:**
    *   Vá em **Settings > Secrets and variables > Actions**.
    *   Adicione o seu `OPENAI_API_KEY` em **New repository secret**.
5.  **Ativar Automação:**
    *   O arquivo `.github/workflows/radar-ninja-hourly.yml` já está configurado para rodar de hora em hora.
    *   Vá na aba **Actions** do GitHub e clique em "Enable Workflows" se necessário.

## 🛠️ Estrutura do Motor

*   `scripts/`: Toda a inteligência de busca, score, deduplicação e geração de conteúdo.
*   `templates/`: Layouts da homepage e páginas de produtos.
*   `assets/`: CSS (Blue Premium), JS dinâmico e imagens.
*   `run_bot_24_7.sh`: O script mestre que orquestra tudo.

## 🛡️ Proteção Anti-Duplicados
O robô já vem com o **Escudo Ativo** habilitado no `sync_database.py` e `deep_clean_duplicates.py`. Ele vai garantir que seu novo site cresça de forma limpa e organizada.

---
**Boa sorte com seu novo Radar Ninja!** 🚀
