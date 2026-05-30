const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  categories: [
    { name: 'Celulares', queries: ['iphone', 'samsung galaxy'] },
    { name: 'Games', queries: ['playstation 5'] }
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
    console.log(`📸 Imagem: ${fileName}`);
    return `images/produtos/${fileName}`;
  } catch (err) { return null; }
}

async function getMLProducts(query, category) {
  const products = [];
  try {
    console.log(`🔍 Buscando ML API: ${query}`);
    // Endpoint de busca mais direto
    const res = await axios.get(`https://api.mercadolibre.com/sites/MLB/search?q=${encodeURIComponent(query)}&limit=10`, {
        timeout: 10000
    });
    
    if (res.data && res.data.results) {
      console.log(`✅ API retornou ${res.data.results.length} resultados.`);
      for (const item of res.data.results) {
        products.push({
          id: 'ml-' + item.id,
          name: item.title,
          price: item.price,
          img: item.thumbnail.replace('-I.jpg', '-O.jpg'),
          url: item.permalink,
          store: 'mercadolivre',
          category
        });
      }
    }
  } catch (e) { 
    console.log(`❌ Erro ML API: ${e.message}`); 
  }
  return products;
}

async function run() {
  console.log('🚀 Scanner API Iniciado');
  const all = [];
  for (const c of CONFIG.categories) {
    for (const q of c.queries) {
      const ml = await getMLProducts(q, c.name);
      all.push(...ml);
    }
  }
  
  console.log(`📦 Processando ${all.length} produtos...`);
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
