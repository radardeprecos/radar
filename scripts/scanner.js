const axios = require('axios');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

const productsToScrape = [
  {
    id: "ml-ps5-slim",
    name: "Console PlayStation 5 Slim + 2 Jogos",
    price: 3499.00,
    originalPrice: 4499.00,
    discount: 22,
    store: "mercadolivre",
    category: "Games",
    imgUrl: "https://http2.mlstatic.com/D_NQ_NP_2X_661556-MLA74332204561_022024-O.webp",
    url: "https://www.mercadolivre.com.br/console-playstation-5-slim-cor-branco/p/MLB27953234"
  },
  {
    id: "ml-iphone-15",
    name: "Apple iPhone 15 (128 GB) - Preto",
    price: 4699.00,
    originalPrice: 7299.00,
    discount: 35,
    store: "mercadolivre",
    category: "Celulares",
    imgUrl: "https://m.media-amazon.com/images/I/71d7rfSl0wL._AC_SL1500_.jpg",
    url: "https://www.mercadolivre.com.br/apple-iphone-15-128-gb-preto/p/MLB27641215"
  },
  {
    id: "ml-s24-ultra",
    name: "Samsung Galaxy S24 Ultra 512GB - Titânio",
    price: 6499.00,
    originalPrice: 9999.00,
    discount: 35,
    store: "mercadolivre",
    category: "Celulares",
    imgUrl: "https://m.media-amazon.com/images/I/71Rov66uLhL._AC_SL1500_.jpg",
    url: "https://www.mercadolivre.com.br/samsung-galaxy-s24-ultra-5g-512gb-titnio/p/MLB33678310"
  }
];

async function cacheImage(url, id) {
  if (!url) return null;
  const fileName = `${id}.webp`;
  const filePath = path.join(CONFIG.imageDir, fileName);
  try {
    await fs.ensureDir(CONFIG.imageDir);
    const response = await axios({ 
      url, 
      method: 'GET', 
      responseType: 'arraybuffer', 
      timeout: 15000, 
      headers: { 'User-Agent': CONFIG.userAgent } 
    });
    await sharp(response.data).resize(400, 400, { fit: 'inside' }).webp().toFile(filePath);
    console.log(`📸 Imagem salva: ${fileName}`);
    return `images/produtos/${fileName}`;
  } catch (err) { 
    console.log(`❌ Erro ao baixar ${url}: ${err.message}`);
    return null; 
  }
}

async function run() {
  console.log('🚀 Scanner de Imagens Iniciado');
  const final = [];
  
  for (const p of productsToScrape) {
    console.log(`🔍 Processando: ${p.name}`);
    const localPath = await cacheImage(p.imgUrl, p.id);
    p.image = localPath || p.imgUrl;
    p.isLowestPrice = true;
    p.lowestPrice = p.price;
    delete p.imgUrl;
    final.push(p);
  }

  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, final, { spaces: 2 });
  console.log(`✅ Sucesso: ${final.length} produtos processados.`);
}

run();
