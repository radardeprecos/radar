/**
 * RADAR DE PREÇOS — Robô Scanner (Versão FINAL ROBUSTA)
 * Cache local de imagens em /images/produtos/ e extração de permalinks reais.
 */

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

// ===== CONFIG =====
const CONFIG = {
  affiliateAmazon: 'radar041-20',
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  historyDir: path.join(__dirname, '../data/history/'),
  imageDir: path.join(__dirname, '../images/produtos/'), // Caminho solicitado pelo usuário
  categories: [
    { name: 'Celulares', queries: ['iphone', 'samsung galaxy', 'xiaomi'] },
    { name: 'Informática', queries: ['notebook', 'ssd', 'monitor'] },
    { name: 'Eletrodomésticos', queries: ['air fryer', 'geladeira'] },
    { name: 'Games', queries: ['playstation 5', 'nintendo switch'] }
  ],
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

const delay = ms => new Promise(res => setTimeout(res, ms));

function slugify(text) {
  return text.toString().toLowerCase().trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w-]+/g, '')
    .replace(/--+/g, '-');
}

/**
 * Baixa uma imagem, converte para WebP e salva localmente em /images/produtos/
 */
async function cacheImage(url, id) {
  if (!url) return null;
  const fileName = `${id}.webp`;
  const filePath = path.join(CONFIG.imageDir, fileName);
  const publicPath = `images/produtos/${fileName}`; // Caminho para o HTML

  try {
    await fs.ensureDir(CONFIG.imageDir);
    
    // Tenta baixar a imagem
    const response = await axios({
      url, method: 'GET', responseType: 'arraybuffer', timeout: 15000,
      headers: { 'User-Agent': CONFIG.userAgent }
    });

    await sharp(response.data)
      .resize(400, 400, { fit: 'inside', withoutEnlargement: true })
      .webp({ quality: 80 })
      .toFile(filePath);

    console.log(`📸 Imagem salva: ${publicPath}`);
    return publicPath;
  } catch (err) {
    console.log(`⚠️ Falha ao baixar imagem: ${url} - ${err.message}`);
    return null; 
  }
}

// ===== SCRAPERS =====

async function scrapeAmazon(query, category) {
  const products = [];
  try {
    const url = `https://www.amazon.com.br/s?k=${encodeURIComponent(query)}`;
    const { data } = await axios.get(url, { headers: { 'User-Agent': CONFIG.userAgent }, timeout: 15000 });
    const $ = cheerio.load(data);
    $('.s-result-item[data-component-type="s-search-result"]').each((i, el) => {
      if (i >= 5) return;
      const name = $(el).find('h2 span').text().trim();
      const priceWhole = $(el).find('.a-price-whole').text().replace(/[.,]/g, '').trim();
      const priceFraction = $(el).find('.a-price-fraction').text().trim() || '00';
      const price = parseFloat(`${priceWhole}.${priceFraction}`);
      const imageSrc = $(el).find('.s-image').attr('src');
      let link = $(el).find('h2 a').attr('href');
      if (name && price && link) {
        if (!link.startsWith('http')) link = 'https://www.amazon.com.br' + link;
        link = link.split('?')[0];
        const id = 'amz-' + slugify(name.substring(0, 20) + '-' + price);
        products.push({ id, name, price, imageSrc, url: link, store: 'amazon', category });
      }
    });
  } catch (err) {}
  return products;
}

async function scrapeMercadoLivre(query, category) {
  const products = [];
  try {
    const url = `https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`;
    const { data } = await axios.get(url, { headers: { 'User-Agent': CONFIG.userAgent }, timeout: 15000 });
    const $ = cheerio.load(data);
    $('.ui-search-result__wrapper, .ui-search-layout__item').each((i, el) => {
      if (i >= 5) return;
      const name = $(el).find('h2').text().trim() || $(el).find('.ui-search-item__title').text().trim();
      const priceText = $(el).find('.andes-money-amount__fraction').first().text().replace(/\./g, '').trim();
      const priceCents = $(el).find('.andes-money-amount__cents').first().text().trim() || '00';
      const price = parseFloat(`${priceText}.${priceCents}`);
      const imageSrc = $(el).find('img').attr('data-src') || $(el).find('img').attr('src');
      let link = $(el).find('a').attr('href');
      if (name && price && link) {
        link = link.split('#')[0].split('?')[0];
        const id = 'ml-' + slugify(name.substring(0, 20) + '-' + price);
        products.push({ id, name, price, imageSrc, url: link, store: 'mercadolivre', category });
      }
    });
  } catch (err) {}
  return products;
}

// ===== PROCESSING =====

async function run() {
  console.log('🚀 Iniciando Scanner...');
  const allProducts = [];
  for (const cat of CONFIG.categories) {
    for (const query of cat.queries) {
      console.log(`🔍 Buscando: ${query}`);
      const ml = await scrapeMercadoLivre(query, cat.name);
      const amz = await scrapeAmazon(query, cat.name);
      allProducts.push(...ml, ...amz);
    }
  }

  const finalProducts = [];
  for (const p of allProducts) {
    // Baixa imagem localmente
    const localImg = await cacheImage(p.imageSrc, p.id);
    p.image = localImg || p.imageSrc;
    delete p.imageSrc;
    
    // Histórico de preço
    const historyFile = path.join(CONFIG.historyDir, `${p.id}.json`);
    let history = [];
    if (await fs.exists(historyFile)) history = await fs.readJson(historyFile);
    history.push({ price: p.price, date: new Date().toISOString() });
    if (history.length > 30) history.shift();
    await fs.ensureDir(CONFIG.historyDir);
    await fs.writeJson(historyFile, history);
    
    p.lowestPrice = Math.min(...history.map(h => h.price));
    p.isLowestPrice = p.price <= p.lowestPrice;
    finalProducts.push(p);
  }

  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, finalProducts.slice(0, 100), { spaces: 2 });
  console.log(`✅ Finalizado! ${finalProducts.length} produtos processados.`);
}

run();
