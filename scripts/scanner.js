const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  historyDir: path.join(__dirname, '../data/history/'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  categories: [
    { name: 'Celulares', queries: ['iphone', 'samsung galaxy'] },
    { name: 'Games', queries: ['playstation 5', 'nintendo switch'] }
  ],
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

async function cacheImage(url, id) {
  if (!url) return null;
  const fileName = `${id}.webp`;
  const filePath = path.join(CONFIG.imageDir, fileName);
  try {
    await fs.ensureDir(CONFIG.imageDir);
    const response = await axios({ url, method: 'GET', responseType: 'arraybuffer', timeout: 15000, headers: { 'User-Agent': CONFIG.userAgent } });
    await sharp(response.data).resize(400, 400, { fit: 'inside' }).webp().toFile(filePath);
    return `images/produtos/${fileName}`;
  } catch (err) { return null; }
}

async function scrapeML(query, category) {
  const products = [];
  try {
    const { data } = await axios.get(`https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`, { headers: { 'User-Agent': CONFIG.userAgent } });
    const $ = cheerio.load(data);
    $('.ui-search-result__wrapper, .ui-search-layout__item').each((i, el) => {
      if (i >= 5) return;
      const name = $(el).find('.ui-search-item__title').text().trim();
      const price = parseFloat($(el).find('.andes-money-amount__fraction').first().text().replace(/\./g, ''));
      const img = $(el).find('img').attr('data-src') || $(el).find('img').attr('src');
      const link = $(el).find('a.ui-search-link').attr('href');
      if (name && price && link) products.push({ id: 'ml-' + i + Date.now(), name, price, img, url: link.split('?')[0], store: 'mercadolivre', category });
    });
  } catch (e) {}
  return products;
}

async function scrapeAmz(query, category) {
  const products = [];
  try {
    const { data } = await axios.get(`https://www.amazon.com.br/s?k=${encodeURIComponent(query)}`, { headers: { 'User-Agent': CONFIG.userAgent } });
    const $ = cheerio.load(data);
    $('.s-result-item[data-component-type="s-search-result"]').each((i, el) => {
      if (i >= 5) return;
      const name = $(el).find('h2 span').text().trim();
      const price = parseFloat($(el).find('.a-price-whole').first().text().replace(/[.,]/g, ''));
      const img = $(el).find('.s-image').attr('src');
      const link = $(el).find('h2 a').attr('href');
      if (name && price && link) products.push({ id: 'amz-' + i + Date.now(), name, price, img, url: 'https://www.amazon.com.br' + link.split('?')[0], store: 'amazon', category });
    });
  } catch (e) {}
  return products;
}

async function run() {
  const all = [];
  for (const c of CONFIG.categories) {
    for (const q of c.queries) {
      all.push(...(await scrapeML(q, c.name)));
      all.push(...(await scrapeAmz(q, c.name)));
    }
  }
  const final = [];
  for (const p of all) {
    const local = await cacheImage(p.img, p.id);
    if (local) { p.image = local; final.push(p); }
  }
  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, final, { spaces: 2 });
}
run();
