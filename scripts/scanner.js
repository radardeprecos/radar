const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
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
    console.log(`📸 Imagem salva: ${fileName}`);
    return `images/produtos/${fileName}`;
  } catch (err) { 
    console.log(`❌ Erro imagem ${id}: ${err.message}`);
    return null; 
  }
}

async function scrapeML(query, category) {
  const products = [];
  try {
    console.log(`🔍 ML: ${query}`);
    const { data } = await axios.get(`https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`, { headers: { 'User-Agent': CONFIG.userAgent } });
    const $ = cheerio.load(data);
    // Seletores extremamente genéricos
    $('.ui-search-result__wrapper, .ui-search-layout__item, .ui-search-result').each((i, el) => {
      if (i >= 8) return;
      const name = $(el).find('h2').text().trim();
      const priceVal = $(el).find('.andes-money-amount__fraction').first().text().replace(/\./g, '');
      const price = parseFloat(priceVal);
      const img = $(el).find('img').attr('data-src') || $(el).find('img').attr('src');
      const link = $(el).find('a').attr('href');
      
      if (name && price && link) {
        console.log(`📦 Encontrado: ${name.substring(0, 30)}...`);
        products.push({ id: 'ml-' + slugify(name.substring(0, 10)) + i, name, price, img, url: link.split('?')[0], store: 'mercadolivre', category });
      }
    });
  } catch (e) { console.log(`❌ Erro ML: ${e.message}`); }
  return products;
}

function slugify(t) { return t.toLowerCase().replace(/\s+/g, '-').replace(/[^\w-]+/g, ''); }

async function run() {
  console.log('🚀 Scanner Iniciado');
  const all = [];
  for (const c of CONFIG.categories) {
    for (const q of c.queries) {
      const results = await scrapeML(q, c.name);
      all.push(...results);
    }
  }
  
  const final = [];
  for (const p of all) {
    const local = await cacheImage(p.img, p.id);
    if (local) { p.image = local; final.push(p); }
  }
  
  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, final, { spaces: 2 });
  console.log(`✅ Sucesso: ${final.length} produtos.`);
}
run();
