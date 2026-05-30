# 🚀 Guia de Deployment — Radar de Preços

## Opção 1: GitHub Pages (Recomendado - Gratuito)

O site já está configurado para deploy automático no GitHub Pages.

### Como funciona:

1. Cada push para `main` atualiza o site automaticamente
2. GitHub Actions roda o scanner a cada 30 minutos
3. Resultados são publicados em: `https://radardeprecos.github.io/radar/`

### Configuração:

1. Ir em **Settings → Pages**
2. Source: `Deploy from a branch`
3. Branch: `main` / folder: `/ (root)`
4. Salvar

**Pronto!** O site está ao vivo.

---

## Opção 2: VPS Linux (Produção)

Para deploy em servidor próprio com domínio customizado.

### Requisitos

- Ubuntu 22.04 LTS ou superior
- Node.js 18+
- Git
- Nginx (opcional, para reverse proxy)

### Passo 1: Preparar o Servidor

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Instalar Git
sudo apt install -y git

# Criar diretório do projeto
mkdir -p /var/www/radar
cd /var/www/radar
```

### Passo 2: Clonar Repositório

```bash
# Clonar com HTTPS
git clone https://github.com/radardeprecos/radar.git .

# Ou com SSH (se tiver chave configurada)
git clone git@github.com:radardeprecos/radar.git .
```

### Passo 3: Instalar Dependências

```bash
npm install
```

### Passo 4: Configurar Cron para Rodar a Cada 30 Minutos

```bash
# Editar crontab
crontab -e

# Adicionar linha:
*/30 * * * * cd /var/www/radar && node scripts/scanner.js >> /var/www/radar/data/logs/cron.log 2>&1
```

### Passo 5: Servir com Nginx (Opcional)

```bash
# Instalar Nginx
sudo apt install -y nginx

# Criar arquivo de configuração
sudo nano /etc/nginx/sites-available/radar
```

Adicionar:

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;

    root /var/www/radar;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|webp|json)$ {
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

Ativar:

```bash
sudo ln -s /etc/nginx/sites-available/radar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Passo 6: SSL com Let's Encrypt (Recomendado)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Gerar certificado
sudo certbot --nginx -d seu-dominio.com.br

# Auto-renovação
sudo systemctl enable certbot.timer
```

### Passo 7: Configurar Auto-Atualização

```bash
# Criar script de atualização
cat > /var/www/radar/update.sh << 'EOF'
#!/bin/bash
cd /var/www/radar
git pull origin main
npm install
npm start
EOF

chmod +x /var/www/radar/update.sh

# Adicionar ao crontab para rodar a cada 30 min:
*/30 * * * * /var/www/radar/update.sh
```

---

## Opção 3: Docker

### Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copiar arquivos
COPY package*.json ./
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY assets/ ./assets/
COPY index.html .
COPY config.json .

# Instalar dependências
RUN npm install

# Expor porta (se usar servidor Node)
EXPOSE 3000

# Comando padrão
CMD ["npm", "start"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  radar:
    build: .
    container_name: radar-precos
    volumes:
      - ./data:/app/data
      - ./images:/app/images
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    container_name: radar-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data:/usr/share/nginx/html:ro
      - ./images:/usr/share/nginx/html/images:ro
    depends_on:
      - radar
    restart: unless-stopped
```

Deploy:

```bash
docker-compose up -d
```

---

## Monitoramento

### Verificar Status

```bash
# Ver últimos logs
tail -f /var/www/radar/data/logs/log-*.json

# Ver cron logs
tail -f /var/www/radar/data/logs/cron.log

# Verificar processo Node
ps aux | grep node

# Verificar uso de disco
du -sh /var/www/radar
```

### Alertas

Configure alertas para:
- ❌ Falha no scanner
- ⚠️ Sem produtos publicados
- 🔴 Erro de conexão com APIs

---

## Backup

### Backup Automático

```bash
# Script de backup
cat > /var/www/radar/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/radar"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/radar-$(date +%Y%m%d-%H%M%S).tar.gz \
  /var/www/radar/data \
  /var/www/radar/images
EOF

chmod +x /var/www/radar/backup.sh

# Executar diariamente
0 2 * * * /var/www/radar/backup.sh
```

### Restaurar Backup

```bash
cd /var/www/radar
tar -xzf /backups/radar/radar-YYYYMMDD-HHMMSS.tar.gz
```

---

## Troubleshooting

### Scanner não roda

```bash
# Testar manualmente
cd /var/www/radar
node scripts/scanner.js

# Ver erros
npm start 2>&1 | tee debug.log
```

### Permissões

```bash
# Corrigir permissões
sudo chown -R www-data:www-data /var/www/radar
sudo chmod -R 755 /var/www/radar
sudo chmod -R 775 /var/www/radar/data
```

### Espaço em disco

```bash
# Limpar logs antigos
find /var/www/radar/data/logs -mtime +30 -delete

# Limpar imagens antigas
find /var/www/radar/images -mtime +60 -delete
```

---

## Performance

### Otimizações

1. **Gzip Compression** - Reduz tamanho de arquivos
2. **Cache Headers** - Navegador cacheia assets
3. **CDN** - Servir imagens via CloudFlare
4. **Minificação** - CSS/JS minificados
5. **Lazy Loading** - Carregar imagens sob demanda

### Métricas

Monitorar:
- Tempo de resposta (< 2s)
- Tempo de carregamento (< 3s)
- Taxa de erro (< 1%)
- Uptime (> 99.9%)

---

## Segurança

### Checklist

- ✅ Firewall ativado (UFW)
- ✅ SSH com chave (sem senha)
- ✅ Fail2ban para brute force
- ✅ SSL/TLS (HTTPS)
- ✅ Headers de segurança
- ✅ Rate limiting
- ✅ Logs auditados

### Firewall

```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Suporte

Para problemas de deployment:

1. Verificar logs: `tail -f /var/www/radar/data/logs/*`
2. Testar manualmente: `node scripts/scanner.js`
3. Verificar permissões: `ls -la /var/www/radar/`
4. Consultar GitHub Issues

---

**Última atualização:** 2026-05-30
