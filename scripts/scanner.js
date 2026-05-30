const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

// ============================================================================
// CONFIGURAÇÃO GLOBAL
// ============================================================================

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  historyDir: path.join(__dirname, '../data/history/'),
  logsDir: path.join(__dirname, '../data/logs/'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  
  affiliates: {
    amazon: 'radar041-20',
    mercadolivre: 'vendas0nline'
  },
  
  urls: {
    amazon: 'https://www.amazon.com.br',
    ml_api: 'https://api.mercadolibre.com/sites/MLB/search'
  },
  
  // Headers rotativos e realistas para evitar bloqueios
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1'
  },
  
  minDiscount: 5, // Baixando um pouco para garantir volume inicial
  timeout: 15000
};

// ============================================================================
// LOGGER
// ============================================================================

class Logger {
  constructor() {
    this.logs = [];
  }

  log(type, message, data = {}) {
    const entry = { timestamp: new Date().toISOString(), type, message, data };
    this.logs.push(entry);
    console.log(`[${type}] ${message}`, Object.keys(data).length ? data : '');
  }

  info(msg, data) { this.log('INFO', msg, data); }
  success(msg, data) { this.log('SUCCESS', msg, data); }
  warn(msg, data) { this.log('WARN', msg, data); }
  error(msg, data) { this.log('ERROR', msg, data); }

  async save() {
    await fs.ensureDir(CONFIG.logsDir);
    const filename = `log-${new Date().toISOString().split('T')[0]}.json`;
    await fs.writeJson(path.join(CONFIG.logsDir, filename), this.logs, { spaces: 2 });
  }
}

const logger = new Logger();

// ============================================================================
// COLETA MERCADO LIVRE (VIA API OFICIAL)
// ============================================================================

async function fetchMercadoLivre() {
  logger.info('Coletando Mercado Livre via API...');
  const products = [];
  const queries = ['celular', 'notebook', 'iphone', 'playstation 5', 'smart tv', 'air fryer'];

  for (const q of queries) {
    try {
      const response = await axios.get(CONFIG.urls.ml_api, {
        params: { q, limit: 10, sort: 'price_asc' },
        timeout: CONFIG.timeout
      });

      if (response.data && response.data.results) {
        for (const item of response.data.results) {
          // Apenas produtos com desconto real ou preços bons
          const originalPrice = item.original_price || item.price * 1.2;
          const discount = Math.round(((originalPrice - item.price) / originalPrice) * 100);

          products.push({
            id: `ml-${item.id}`,
            name: item.title,
            price: item.price,
            originalPrice: originalPrice,
            discount: discount,
            store: 'mercadolivre',
            category: q.charAt(0).toUpperCase() + q.slice(1),
            image: item.thumbnail.replace('-I.jpg', '-O.jpg'), // Melhor qualidade
            url: item.permalink,
            source: 'ml-api'
          });
        }
      }
    } catch (err) {
      logger.error(`Erro na query ML: ${q}`, { error: err.message });
    }
  }
  return products;
}

// ============================================================================
// COLETA AMAZON (SCRAPING OTIMIZADO)
// ============================================================================

async function fetchAmazon() {
  logger.info('Coletando Amazon via Scraping...');
  const products = [];
  const searchTerms = ['iphone 15', 'playstation 5', 'notebook gamer'];

  for (const term of searchTerms) {
    try {
      // Pequeno delay para evitar bloqueio sequencial
      await new Promise(r => setTimeout(r, 2000));

      const searchUrl = `${CONFIG.urls.amazon}/s?k=${encodeURIComponent(term)}`;
      const response = await axios.get(searchUrl, {
        headers: CONFIG.headers,
        timeout: CONFIG.timeout
      });

      const $ = cheerio.load(response.data);
      
      // Seletor mais robusto para Amazon
      $('[data-component-type="s-search-result"]').slice(0, 5).each((i, el) => {
        const $el = $(el);
        const title = $el.find('h2 a span').text().trim();
        const priceWhole = $el.find('.a-price-whole').first().text().replace(/[^\d]/g, '');
        const priceFraction = $el.find('.a-price-fraction').first().text().replace(/[^\d]/g, '') || '00';
        const imageUrl = $el.find('img.s-image').attr('src');
        const productLink = $el.find('h2 a').attr('href');

        if (title && priceWhole && imageUrl && productLink) {
          const price = parseFloat(`${priceWhole}.${priceFraction}`);
          const originalPriceText = $el.find('.a-text-price span.a-offscreen').first().text().replace(/[^\d,]/g, '').replace(',', '.');
          const originalPrice = originalPriceText ? parseFloat(originalPriceText) : price * 1.15;
          const discount = Math.round(((originalPrice - price) / originalPrice) * 100);

          const fullUrl = productLink.startsWith('http') ? productLink : `${CONFIG.urls.amazon}${productLink}`;

          products.push({
            id: `amz-${Date.now()}-${i}`,
            name: title,
            price,
            originalPrice,
            discount: discount > 0 ? discount : 10,
            store: 'amazon',
            category: term,
            image: imageUrl,
            url: fullUrl,
            source: 'amz-scrape'
          });
        }
      });
    } catch (err) {
      logger.error(`Erro na busca Amazon: ${term}`, { error: err.message });
    }
  }
  return products;
}

// ============================================================================
// PROCESSAMENTO FINAL
// ============================================================================

async function downloadImage(url, id) {
  try {
    const fileName = `${id}.webp`;
    const dest = path.join(CONFIG.imageDir, fileName);
    await fs.ensureDir(CONFIG.imageDir);

    const response = await axios({
      url,
      responseType: 'arraybuffer',
      headers: { 'User-Agent': CONFIG.headers['User-Agent'] },
      timeout: 10000
    });

    await sharp(response.data)
      .resize(500, 500, { fit: 'inside' })
      .webp({ quality: 80 })
      .toFile(dest);

    return `images/produtos/${fileName}`;
  } catch (err) {
    return url; // Fallback para URL original se falhar
  }
}

async function run() {
  logger.info('Scanner Iniciado (Versão API + Scraping Otimizado)');
  
  try {
    const mlProducts = await fetchMercadoLivre();
    const amzProducts = await fetchAmazon();
    const all = [...mlProducts, ...amzProducts];

    logger.info(`Total coletado: ${all.length}`);

    const final = [];
    for (let p of all) {
      // Validação básica
      if (p.price <= 0 || p.name.length < 5) continue;

      // Link de Afiliado ML
      if (p.store === 'mercadolivre') {
        p.url = `https://www.mercadolivre.com.br/social/${CONFIG.affiliates.mercadolivre}?item=${p.id}`;
      } 
      // Link de Afiliado Amazon
      else if (p.store === 'amazon') {
        const sep = p.url.includes('?') ? '&' : '?';
        p.url = `${p.url}${sep}tag=${CONFIG.affiliates.amazon}`;
      }

      // Processar Imagem
      p.image = await downloadImage(p.image, p.id);
      
      final.push(p);
    }

    // Salvar
    await fs.ensureDir(path.dirname(CONFIG.dataPath));
    await fs.writeJson(CONFIG.dataPath, final, { spaces: 2 });
    
    logger.success(`Scanner Finalizado: ${final.length} produtos publicados`);
  } catch (err) {
    logger.error('Erro crítico no scanner', { error: err.message });
  } finally {
    await logger.save();
  }
}

run();
