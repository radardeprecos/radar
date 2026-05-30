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
    { name: 'Games', queries: ['playstation 5'] }
  ]
};

const headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
  'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
  'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
  'Sec-Ch-Ua-Mobile': '?0',
  'Sec-Ch-Ua-Platform': '"Windows"',
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'none',
  'Sec-Fetch-User': '?1',
  'Upgrade-Insecure-Requests': '1'
};

async function cacheImage(url, id) {
  if (!url) return null;
  const fileName = `${id}.webp`;
  const filePath = path.join(CONFIG.imageDir, fileName);
  try {
    await fs.ensureDir(CONFIG.imageDir);
    const response = await axios({ url, method: 'GET', responseType: 'arraybuffer', timeout: 15000, headers });
    await sharp(response.data).resize(400, 400, { fit: 'inside' }).webp().toFile(filePath);
    console.log(`📸 Imagem: ${fileName}`);
    return `images/produtos/${fileName}`;
  } catch (err) { return null; }
}

async function getMLProducts(query, category) {
  const products = [];
  try {
    console.log(`🔍 Buscando ML: ${query}`);
    const url = `https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`;
    const { data } = await axios.get(url, { headers, timeout: 15000 });
    const $ = cheerio.load(data);
    
    $('.ui-search-result__wrapper, .ui-search-layout__item').each((i, el) => {
      if (i >= 5) return;
      const name = $(el).find('h2').text().trim() || $(el).find('.ui-search-item__title').text().trim();
      const priceText = $(el).find('.andes-money-amount__fraction').first().text().replace(/\./g, '');
      const price = parseFloat(priceText);
      const img = $(el).find('img').attr('data-src') || $(el).find('img').attr('src');
      let link = $(el).find('a').attr('href');
      
      if (name && price && link) {
        link = link.split('#')[0].split('?')[0];
        products.push({
          id: 'ml-' + i + Date.now(),
          name, price, img, url: link,
          store: 'mercadolivre', category
        });
      }
    });
    console.log(`✅ Encontrados ${products.length} itens para ${query}`);
  } catch (e) { 
    console.log(`❌ Erro ML (${query}): ${e.message}`); 
  }
  return products;
}

async function run() {
  console.log('🚀 Scanner Iniciado');
  const all = [];
  for (const c of CONFIG.categories) {
    for (const q of c.queries) {
      const ml = await getMLProducts(q, c.name);
      all.push(...ml);
    }
  }
  
  console.log(`📦 Total de produtos para processar: ${all.length}`);
  const final = [];
  for (const p of all) {
    const local = await cacheImage(p.img, p.id);
    if (local) { 
        p.image = local; 
        final.push(p); 
    } else {
        p.image = p.img;
        final.push(p);
    }
  }
  
  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, final, { spaces: 2 });
  console.log(`✅ Sucesso Final: ${final.length} produtos salvos.`);
}
run();
