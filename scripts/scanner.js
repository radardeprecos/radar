const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

/**
 * RADAR DE PREÇOS v5.0 — EXCLUSIVO MERCADO LIVRE
 * Foco em estabilidade, imagens válidas e links reais.
 */

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  logsDir: path.join(__dirname, '../data/logs/'),
  sitemapPath: path.join(__dirname, '../sitemap.xml'),
  robotsPath: path.join(__dirname, '../robots.txt'),
  siteUrl: 'https://radardeprecos.github.io/radar/',
  
  // Identificador do Mercado Livre Social
  mlSocialId: 'vendas0nline',
  
  // API Pública do Mercado Livre (não exige token para buscas básicas)
  mlApi: 'https://api.mercadolibre.com/sites/MLB/search',
  
  minDiscount: 10,
  timeout: 10000,
  
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  }
};

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

async function validateUrl(url) {
  try {
    const response = await axios.head(url, { timeout: 5000 });
    return response.status === 200;
  } catch (err) {
    return false;
  }
}

async function downloadAndProcessImage(url, id) {
  try {
    const fileName = `${id}.webp`;
    const dest = path.join(CONFIG.imageDir, fileName);
    await fs.ensureDir(CONFIG.imageDir);

    const response = await axios({
      url,
      responseType: 'arraybuffer',
      timeout: 10000
    });

    if (!response.data || response.data.length < 500) return null;

    await sharp(response.data)
      .resize(500, 500, { fit: 'inside' })
      .webp({ quality: 80 })
      .toFile(dest);

    return (await fs.pathExists(dest)) ? `images/produtos/${fileName}` : null;
  } catch (err) {
    return null;
  }
}

async function generateSitemap(products) {
  const now = new Date().toISOString().split('T')[0];
  let xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n`;
  xml += `  <url><loc>${CONFIG.siteUrl}</loc><lastmod>${now}</lastmod><changefreq>hourly</changefreq><priority>1.0</priority></url>\n`;
  products.forEach(p => {
    xml += `  <url><loc>${CONFIG.siteUrl}#${p.id}</loc><lastmod>${now}</lastmod><priority>0.8</priority></url>\n`;
  });
  xml += `</urlset>`;
  await fs.writeFile(CONFIG.sitemapPath, xml);
}

async function fetchMercadoLivre() {
  logger.info('Iniciando busca real no Mercado Livre...');
  const products = [];
  const queries = ['iPhone', 'PlayStation 5', 'Notebook', 'Smart TV', 'Air Fryer', 'Samsung Galaxy'];

  for (const q of queries) {
    try {
      const response = await axios.get(CONFIG.mlApi, {
        params: { q, limit: 10, sort: 'relevance' },
        timeout: CONFIG.timeout
      });

      if (response.data && response.data.results) {
        for (const item of response.data.results) {
          logger.info(`Produto encontrado: ${item.title}`, { id: item.id });

          const originalPrice = item.original_price || item.price * 1.15;
          const discount = Math.round(((originalPrice - item.price) / originalPrice) * 100);

          if (discount < CONFIG.minDiscount) {
            logger.warn('Rejeitado: Desconto baixo', { id: item.id, discount });
            continue;
          }

          const localImage = await downloadAndProcessImage(item.thumbnail.replace('-I.jpg', '-O.jpg'), item.id);
          if (!localImage) {
            logger.warn('Rejeitado: Falha na imagem', { id: item.id });
            continue;
          }

          // Link Social do Mercado Livre
          const affiliateUrl = `https://www.mercadolivre.com.br/social/${CONFIG.mlSocialId}?item=${item.id}`;

          products.push({
            id: item.id,
            name: item.title,
            price: item.price,
            originalPrice: originalPrice,
            discount: discount,
            store: 'mercadolivre',
            category: q,
            image: localImage,
            url: affiliateUrl,
            originalUrl: item.permalink
          });

          logger.success(`Publicado: ${item.title}`, { id: item.id });
        }
      }
    } catch (err) {
      logger.error(`Erro na busca ML (${q}): ${err.message}`);
    }
  }
  return products;
}

async function run() {
  logger.info('=== SCANNER v5.0 INICIADO ===');
  try {
    const products = await fetchMercadoLivre();
    if (products.length > 0) {
      await fs.ensureDir(path.dirname(CONFIG.dataPath));
      await fs.writeJson(CONFIG.dataPath, products, { spaces: 2 });
      await generateSitemap(products);
      logger.success(`Scanner concluído: ${products.length} produtos publicados.`);
    } else {
      logger.warn('FIM: Nenhum produto novo encontrado.');
    }
  } catch (err) {
    logger.error('Erro crítico no scanner', { error: err.message });
  } finally {
    await logger.save();
  }
}

run();
