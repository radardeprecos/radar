/**
 * RADAR DE PREÇOS — Robô Scanner (Versão ROBUSTA com Cache WebP)
 * Busca produtos via Scraping, salva histórico e gera JSON.
 */

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

// ===== CONFIG =====
const CONFIG = {
  affiliateAmazon: 'radar041-20',
  affiliateML: 'https://www.mercadolivre.com.br/social/vendas0nline',
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  historyDir: path.join(__dirname, '../data/history/'),
  imageDir: path.join(__dirname, '../assets/products/'),
  categories: [
    { name: 'Celulares', queries: ['iphone', 'samsung galaxy', 'xiaomi', 'motorola'] },
    { name: 'Informática', queries: ['notebook', 'ssd', 'monitor', 'teclado mecanico'] },
    { name: 'Eletrodomésticos', queries: ['air fryer', 'geladeira', 'maquina de lavar', 'microondas'] },
    { name: 'TV e Vídeo', queries: ['smart tv 4k', 'monitor gamer', 'fire stick'] },
    { name: 'Games', queries: ['playstation 5', 'nintendo switch', 'xbox series', 'controle ps5'] },
    { name: 'Casa', queries: ['robo aspirador', 'jogo de panelas', 'lampada inteligente'] },
    { name: 'Ferramentas', queries: ['furadeira', 'parafusadeira', 'jogo de chaves'] },
    { name: 'Beleza', queries: ['secador de cabelo', 'barbeador eletrico', 'chapinha'] }
  ],
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

// ===== HELPERS =====
const delay = ms => new Promise(res => setTimeout(res, ms));

function slugify(text) {
  return text.toString().toLowerCase().trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w-]+/g, '')
    .replace(/--+/g, '-');
}

/**
 * Baixa uma imagem, converte para WebP e salva localmente.
 */
async function cacheImage(url, id) {
  if (!url) return null;
  const fileName = `${id}.webp`;
  const filePath = path.join(CONFIG.imageDir, fileName);
  const publicPath = `assets/products/${fileName}`;

  try {
    await fs.ensureDir(CONFIG.imageDir);
    const response = await axios({
      url, method: 'GET', responseType: 'arraybuffer', timeout: 15000,
      headers: { 'User-Agent': CONFIG.userAgent }
    });
    await sharp(response.data).resize(400, 400, { fit: 'inside', withoutEnlargement: true }).webp({ quality: 80 }).toFile(filePath);
    return publicPath;
  } catch (err) {
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
    const items = $('.s-result-item[data-component-type="s-search-result"]');
    for (let i = 0; i < items.length; i++) {
      if (i >= 5) break;
      const el = items[i];
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
        const localImage = await cacheImage(imageSrc, id);
        products.push({ id, name, price, image: localImage || imageSrc, url: link, store: 'amazon', category, timestamp: new Date().toISOString() });
      }
    }
  } catch (err) {}
  return products;
}

async function scrapeMercadoLivre(query, category) {
  const products = [];
  try {
    const url = `https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`;
    const { data } = await axios.get(url, { headers: { 'User-Agent': CONFIG.userAgent }, timeout: 15000 });
    const $ = cheerio.load(data);
    const items = $('.ui-search-result__wrapper, .ui-search-layout__item');
    for (let i = 0; i < items.length; i++) {
      if (i >= 8) break;
      const el = items[i];
      const name = $(el).find('h2').text().trim() || $(el).find('.ui-search-item__title').text().trim();
      const priceText = $(el).find('.andes-money-amount__fraction').first().text().replace(/\./g, '').trim();
      const priceCents = $(el).find('.andes-money-amount__cents').first().text().trim() || '00';
      const price = parseFloat(`${priceText}.${priceCents}`);
      const imageSrc = $(el).find('img').attr('data-src') || $(el).find('img').attr('src');
      let link = $(el).find('a').attr('href');
      if (name && price && link) {
        link = link.split('#')[0].split('?')[0];
        const id = 'ml-' + slugify(name.substring(0, 20) + '-' + price);
        const localImage = await cacheImage(imageSrc, id);
        products.push({ id, name, price, image: localImage || imageSrc, url: link, store: 'mercadolivre', category, timestamp: new Date().toISOString() });
      }
    }
  } catch (err) {}
  return products;
}

// ===== DATA PROCESSING =====

async function processProducts(newProducts) {
  let db = [];
  if (await fs.exists(CONFIG.dataPath)) db = await fs.readJson(CONFIG.dataPath);
  for (const p of newProducts) {
    const historyFile = path.join(CONFIG.historyDir, `${p.id}.json`);
    let history = [];
    if (await fs.exists(historyFile)) history = await fs.readJson(historyFile);
    const lastPrice = history.length > 0 ? history[history.length - 1].price : null;
    if (p.price !== lastPrice) {
      history.push({ price: p.price, date: p.timestamp });
      if (history.length > 30) history.shift();
      await fs.ensureDir(CONFIG.historyDir);
      await fs.writeJson(historyFile, history);
    }
    const prices = history.map(h => h.price);
    p.lowestPrice = Math.min(...prices);
    p.isLowestPrice = p.price <= p.lowestPrice;
    p.priceHistory = history;
    const idx = db.findIndex(item => item.id === p.id);
    if (idx >= 0) db[idx] = p; else db.push(p);
  }
  db.sort((a, b) => (b.discount || 0) - (a.discount || 0));
  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, db.slice(0, 100), { spaces: 2 });
}

async function run() {
  console.log('🚀 Iniciando Scanner Radar de Preços...');
  const allNewProducts = [];
  for (const cat of CONFIG.categories) {
    for (const query of cat.queries) {
      const ml = await scrapeMercadoLivre(query, cat.name);
      const amz = await scrapeAmazon(query, cat.name);
      allNewProducts.push(...ml, ...amz);
    }
  }
  if (allNewProducts.length > 0) await processProducts(allNewProducts);
  console.log('✅ Scanner finalizado!');
}

run().catch(err => { process.exit(1); });
