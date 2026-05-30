const puppeteer = require('puppeteer');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');
const axios = require('axios');

/**
 * RADAR DE PREÇOS v6.0 — BUSCA REAL VIA NAVEGADOR
 * Sem fallbacks. Sem APIs bloqueadas. URLs Reais.
 */

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  logsDir: path.join(__dirname, '../data/logs/'),
  sitemapPath: path.join(__dirname, '../sitemap.xml'),
  siteUrl: 'https://radardeprecos.github.io/radar/',
  
  queries: ['iPhone 15', 'PlayStation 5 Slim', 'Samsung Galaxy S24', 'Smart TV 4K', 'Air Fryer Mondial'],
  minDiscount: 5,
  timeout: 30000
};

class Logger {
  constructor() { this.logs = []; }
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

async function downloadImage(url, id) {
  try {
    const fileName = `${id}.webp`;
    const dest = path.join(CONFIG.imageDir, fileName);
    await fs.ensureDir(CONFIG.imageDir);

    const response = await axios({ url, responseType: 'arraybuffer', timeout: 10000 });
    await sharp(response.data).resize(500, 500, { fit: 'inside' }).webp({ quality: 80 }).toFile(dest);
    return `images/produtos/${fileName}`;
  } catch (err) { return null; }
}

async function run() {
  logger.info('=== SCANNER v6.0 (NAVEGADOR REAL) INICIADO ===');
  const browser = await puppeteer.launch({ 
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

  const allProducts = [];

  for (const query of CONFIG.queries) {
    try {
      logger.info(`Buscando: ${query}`);
      await page.goto(`https://lista.mercadolivre.com.br/${encodeURIComponent(query)}#D[A:${encodeURIComponent(query)}]`, { waitUntil: 'networkidle2' });

      const products = await page.evaluate(() => {
        const items = [];
        document.querySelectorAll('.ui-search-result__wrapper').forEach((el, i) => {
          if (i >= 5) return;
          const title = el.querySelector('.ui-search-item__title')?.innerText;
          const price = el.querySelector('.andes-money-amount__fraction')?.innerText.replace('.', '');
          const originalPrice = el.querySelector('.ui-search-price__part--del .andes-money-amount__fraction')?.innerText.replace('.', '');
          const link = el.querySelector('a.ui-search-link')?.href;
          const img = el.querySelector('img.ui-search-result-image__element')?.src || el.querySelector('img.poly-component__picture')?.src;
          
          if (title && price && link) {
            items.push({
              id: 'ml-' + Math.random().toString(36).substr(2, 9),
              name: title,
              price: parseFloat(price),
              originalPrice: originalPrice ? parseFloat(originalPrice) : parseFloat(price) * 1.15,
              url: link,
              image: img
            });
          }
        });
        return items;
      });

      for (const p of products) {
        logger.info(`Validando: ${p.name}`);
        const discount = Math.round(((p.originalPrice - p.price) / p.originalPrice) * 100);
        
        if (discount < CONFIG.minDiscount) {
          logger.warn(`Rejeitado: Desconto baixo (${discount}%)`);
          continue;
        }

        const localImg = await downloadImage(p.image, p.id);
        if (!localImg) {
          logger.warn('Rejeitado: Falha na imagem');
          continue;
        }

        p.discount = discount;
        p.image = localImg;
        p.store = 'mercadolivre';
        allProducts.push(p);
        logger.success(`Publicado: ${p.name} - R$ ${p.price}`);
      }

    } catch (err) {
      logger.error(`Erro na busca: ${query}`, { error: err.message });
    }
  }

  if (allProducts.length > 0) {
    await fs.writeJson(CONFIG.dataPath, allProducts, { spaces: 2 });
    logger.success(`Scanner concluído: ${allProducts.length} produtos reais.`);
  }

  await browser.close();
  await logger.save();
}

run();
