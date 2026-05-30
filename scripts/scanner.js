const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

/**
 * RADAR DE PREÇOS v4.0 — FOCO EXCLUSIVO MERCADO LIVRE
 * Busca real via API pública com headers otimizados.
 */

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  logsDir: path.join(__dirname, '../data/logs/'),
  sitemapPath: path.join(__dirname, '../sitemap.xml'),
  robotsPath: path.join(__dirname, '../robots.txt'),
  siteUrl: 'https://radardeprecos.github.io/radar/',
  
  affiliates: {
    mlId: 'vendas0nline'
  },

  mlApi: 'https://api.mercadolibre.com/sites/MLB/search',
  
  minDiscount: 10,
  timeout: 15000,
  
  // Headers que simulam um navegador real para evitar 403
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Origin': 'https://www.mercadolivre.com.br',
    'Referer': 'https://www.mercadolivre.com.br/'
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
    const response = await axios.get(url, { headers: CONFIG.headers, timeout: 5000 });
    return response.status === 200;
  } catch (err) {
    return false;
  }
}

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
  logger.info('Buscando ofertas reais no Mercado Livre...');
  const products = [];
  const queries = ['iPhone', 'Samsung Galaxy', 'PlayStation 5', 'Notebook Gamer', 'Air Fryer Mondial', 'Smart TV 4K', 'Fone JBL', 'Eletrodomésticos'];

  for (const q of queries) {
    try {
      // Pequeno delay entre queries
      await new Promise(r => setTimeout(r, 1000));

      const response = await axios.get(CONFIG.mlApi, {
        params: { q, limit: 15, sort: 'relevance' },
        headers: CONFIG.headers,
        timeout: CONFIG.timeout
      });

      if (response.data && response.data.results) {
        for (const item of response.data.results) {
          const originalPrice = item.original_price || item.price * 1.15;
          const discount = Math.round(((originalPrice - item.price) / originalPrice) * 100);

          if (discount < CONFIG.minDiscount) continue;

          // Link de Afiliado Social
          const affiliateUrl = `https://www.mercadolivre.com.br/social/${CONFIG.affiliates.mlId}?item=${item.id}`;

          // Imagem de alta qualidade
          const imageUrl = item.thumbnail.replace('-I.jpg', '-O.jpg');
          const localImage = await downloadImage(imageUrl, item.id);
          
          if (!localImage) {
            logger.warn(`Produto rejeitado (sem imagem): ${item.title}`);
            continue;
          }

          products.push({
            id: item.id,
            name: item.title,
            price: item.price,
            originalPrice: originalPrice,
            discount: discount,
            store: 'mercadolivre',
            category: q,
            image: localImage,
            url: affiliateUrl, // Sempre usar o link de afiliado social
            originalUrl: item.permalink
          });

          logger.success(`Produto publicado: ${item.title} (R$ ${item.price})`);
          
          // Limite de 40 produtos no total para manter o site leve
          if (products.length >= 40) break;
        }
      }
      if (products.length >= 40) break;
    } catch (err) {
      logger.error(`Erro na busca ML: ${q}`, { error: err.message });
    }
  }
  return products;
}

async function run() {
  try {
    const products = await fetchMercadoLivre();
    
    if (products.length > 0) {
      await fs.ensureDir(path.dirname(CONFIG.dataPath));
      await fs.writeJson(CONFIG.dataPath, products, { spaces: 2 });
      await generateSitemap(products);
      logger.success(`Scanner concluído: ${products.length} produtos publicados.`);
    } else {
      logger.warn('Nenhum produto encontrado. Verifique os bloqueios.');
    }
  } catch (err) {
    logger.error('Erro crítico no scanner', { error: err.message });
  } finally {
    await logger.save();
  }
}

run();
