# 📊 Radar de Preços — Sistema Automático de Monitoramento de Ofertas

> Plataforma completa que monitora automaticamente preços da Amazon e Mercado Livre, detecta quedas de preço e publica ofertas com o menor preço da história.

## 🎯 Objetivo

Criar um site de comparação de preços que:

- ✅ Coleta produtos automaticamente da Amazon e Mercado Livre
- ✅ Valida cada produto com rigor (imagem + título + preço + URL + desconto)
- ✅ Publica apenas ofertas com desconto ≥ 10% ou menor preço dos últimos 30 dias
- ✅ Mantém histórico completo de preços
- ✅ Roda automaticamente a cada 30 minutos
- ✅ Aplica links de afiliados (Amazon: `radar041-20` | Mercado Livre: `vendas0nline`)
- ✅ Gera SEO automático com meta tags e schema.org
- ✅ Deploy gratuito no GitHub Pages

---

## 🏗️ Arquitetura

```
radar-project/
├── scripts/
│   └── scanner.js          # Robô de coleta e validação
├── data/
│   ├── products/
│   │   └── offers.json     # Produtos publicados (JSON)
│   ├── history/            # Histórico de preços por produto
│   └── logs/               # Logs de execução
├── images/
│   └── produtos/           # Imagens processadas (WebP)
├── assets/
│   ├── css/style.css       # CSS responsivo com tema escuro/claro
│   └── js/app.js           # Frontend com renderização dinâmica
├── index.html              # Página principal
├── package.json            # Dependências
└── .github/workflows/
    └── ROBO-SUPREMO.yml    # GitHub Actions (a cada 30 min)
```

---

## 🤖 Como Funciona

### 1. **Robô de Coleta (scripts/scanner.js)**

O scanner executa a cada 30 minutos via GitHub Actions:

```javascript
// Fluxo:
1. Busca produtos da Amazon (via scraping)
2. Busca produtos do Mercado Livre (via API/scraping)
3. Valida cada produto:
   - ✅ Imagem válida
   - ✅ Título (min 5 caracteres)
   - ✅ Preço > 0
   - ✅ Desconto ≥ 10%
   - ✅ URL válida
   - ✅ Categoria válida
4. Baixa e processa imagens (WebP 500x500)
5. Aplica links de afiliados
6. Salva histórico de preços
7. Publica em data/products/offers.json
8. Faz commit e push automático
```

### 2. **Validação Rigorosa**

Produto é **rejeitado** se:
- ❌ Imagem vazia ou quebrada
- ❌ Link inválido ou genérico (nunca `amazon.com.br` ou `amazon.com.br/s?k=`)
- ❌ Desconto < 10%
- ❌ Página retorna erro
- ❌ Produto indisponível
- ❌ Categoria não corresponde

### 3. **Links de Afiliados**

**Amazon:**
```
https://www.amazon.com.br/PRODUTO?tag=radar041-20
```

**Mercado Livre:**
```
https://www.mercadolivre.com.br/social/vendas0nline?item=PRODUCT_ID
```

### 4. **Histórico de Preços**

Cada produto tem arquivo JSON com histórico dos últimos 30 dias:

```json
[
  {
    "date": "2026-05-30T01:45:00.000Z",
    "price": 2999.00,
    "originalPrice": 3499.00,
    "discount": 14
  }
]
```

---

## 📋 Estrutura de Dados

### Arquivo: `data/products/offers.json`

```json
[
  {
    "id": "ml-ps5-slim-new",
    "name": "Console PlayStation 5 Slim Edição Digital",
    "price": 3399.00,
    "originalPrice": 3999.00,
    "discount": 15,
    "store": "mercadolivre",
    "category": "Games",
    "image": "images/produtos/ml-ps5-slim-new.webp",
    "url": "https://www.mercadolivre.com.br/social/vendas0nline?item=ml-ps5-slim-new",
    "source": "ml-scrape"
  }
]
```

---

## 🚀 Deploy

### GitHub Pages (Automático)

O site está hospedado em:
```
https://radardeprecos.github.io/radar/
```

Cada push atualiza o site automaticamente.

### Executar Localmente

```bash
# Instalar dependências
npm install

# Executar scanner manualmente
npm start

# Abrir index.html no navegador
open index.html
```

---

## ⏰ Agendamento

O robô roda **a cada 30 minutos** via GitHub Actions:

```yaml
# .github/workflows/ROBO-SUPREMO.yml
schedule:
  - cron: '*/30 * * * *'
```

Horários de execução:
- 00:00, 00:30, 01:00, 01:30, ..., 23:30

---

## 📊 Critérios de Publicação

Produto é publicado quando:

| Critério | Descrição |
|----------|-----------|
| **Desconto ≥ 10%** | Redução mínima de 10% no preço |
| **Menor preço (30 dias)** | Preço mais baixo dos últimos 30 dias |
| **Queda significativa** | Redução > 5% em relação à média |

---

## 🎨 Frontend

### Funcionalidades

- 🌙 **Tema Escuro/Claro** - Alternância automática
- 🔍 **Busca em Tempo Real** - Filtro de produtos
- 📱 **Responsivo** - Mobile, tablet, desktop
- ⚡ **Rápido** - Carregamento instantâneo
- ♿ **Acessível** - WCAG 2.1 AA

### Seções

1. **Hero** - Destaque do melhor produto
2. **Grid de Ofertas** - Cards com produtos
3. **Tabela de Ofertas** - Lista detalhada
4. **Top Produtos** - Ranking dos melhores
5. **Categorias** - Navegação por tipo
6. **Alertas** - Cadastro para notificações
7. **Footer** - Links e informações

---

## 🔧 Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| **Frontend** | HTML5 + CSS3 + JavaScript |
| **Coleta** | Node.js + Axios + Cheerio |
| **Imagens** | Sharp (WebP) |
| **Automação** | GitHub Actions |
| **Deploy** | GitHub Pages |
| **Armazenamento** | JSON + Git |

---

## 📝 Logs

Cada execução gera log em `data/logs/log-YYYY-MM-DD.json`:

```json
[
  {
    "timestamp": "2026-05-30T01:45:23.456Z",
    "type": "SUCCESS",
    "message": "Produto publicado",
    "data": {
      "productId": "ml-ps5-slim-new",
      "name": "Console PlayStation 5 Slim",
      "price": 3399.00
    }
  },
  {
    "timestamp": "2026-05-30T01:45:24.789Z",
    "type": "WARN",
    "message": "Produto rejeitado",
    "data": {
      "productId": "amz-xyz",
      "errors": ["Desconto menor que 10%"]
    }
  }
]
```

---

## 🔐 Segurança

- ✅ Validação rigorosa de URLs
- ✅ Verificação de imagens antes de publicar
- ✅ Sanitização de títulos e descrições
- ✅ Timeout em requisições (10s)
- ✅ Logs detalhados de erros
- ✅ Sem armazenamento de dados sensíveis

---

## 📈 SEO

### Meta Tags Automáticas

Cada página de produto tem:

```html
<meta name="description" content="...">
<meta name="keywords" content="...">
<meta property="og:title" content="...">
<meta property="og:image" content="...">
<meta name="twitter:card" content="summary_large_image">
```

### Schema.org

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "...",
  "image": "...",
  "offers": {
    "@type": "Offer",
    "price": "...",
    "priceCurrency": "BRL"
  }
}
```

---

## 🐛 Troubleshooting

### Produtos não aparecem

1. Verificar `data/products/offers.json` existe
2. Verificar logs em `data/logs/`
3. Executar manualmente: `npm start`

### Imagens quebradas

1. Verificar `images/produtos/` tem arquivos
2. Verificar URLs de origem são válidas
3. Verificar permissões de arquivo

### GitHub Actions não roda

1. Verificar `.github/workflows/ROBO-SUPREMO.yml`
2. Verificar Actions está ativado no repositório
3. Verificar token de acesso é válido

---

## 📞 Suporte

Para problemas ou sugestões:

- 📧 Email: [seu-email]
- 💬 Issues: GitHub Issues
- 🐦 Twitter: [@radardeprecos]

---

## 📄 Licença

MIT License - Veja LICENSE para detalhes

---

## 🙏 Créditos

Desenvolvido com ❤️ para encontrar as melhores ofertas do Brasil.

**Última atualização:** 2026-05-30
