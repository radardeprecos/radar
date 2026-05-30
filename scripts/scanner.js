const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

// ============================================================================
// CONFIGURAÇÃO GLOBAL
// ============================================================================

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  sitemapPath: path.join(__dirname, '../sitemap.xml'),
  robotsPath: path.join(__dirname, '../robots.txt'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  siteUrl: 'https://radardeprecos.github.io/radar/',
  
  affiliates: {
    amazon: 'radar041-20',
    mercadolivre: 'vendas0nline'
  }
};

// Dados de Fallback (Ofertas Reais e Validadas)
const fallbackOffers = [
  {
    id: "ml-ps5-slim",
    name: "Console PlayStation 5 Slim Edição Digital",
    price: 3399.00,
    originalPrice: 3999.00,
    store: "mercadolivre",
    category: "Games",
    image: "https://http2.mlstatic.com/D_NQ_NP_2X_661556-MLA74332204561_022024-O.webp",
    url: "https://www.mercadolivre.com.br/console-playstation-5-slim-cor-branco/p/MLB27953234"
  },
  {
    id: "ml-iphone-15",
    name: "Apple iPhone 15 (128 GB) - Preto",
    price: 4699.00,
    originalPrice: 7299.00,
    store: "mercadolivre",
    category: "Celulares",
    image: "https://http2.mlstatic.com/D_NQ_NP_2X_750531-MLU72002393278_092023-O.webp",
    url: "https://www.mercadolivre.com.br/apple-iphone-15-128-gb-preto/p/MLB27303031"
  },
  {
    id: "amz-airpods",
    name: "Apple AirPods Pro (2ª geração) com MagSafe",
    price: 1699.00,
    originalPrice: 2599.00,
    store: "amazon",
    category: "Acessórios",
    image: "https://m.media-amazon.com/images/I/61SUj2W5yXL._AC_SL1500_.jpg",
    url: "https://www.amazon.com.br/Apple-AirPods-Pro-2%C2%AA-gera%C3%A7%C3%A3o/dp/B0BDHWDR12"
  },
  {
    id: "ml-s24-ultra",
    name: "Samsung Galaxy S24 Ultra 512GB - Titânio",
    price: 6199.00,
    originalPrice: 9999.00,
    store: "mercadolivre",
    category: "Celulares",
    image: "https://http2.mlstatic.com/D_NQ_NP_2X_656548-MLU74245645341_012024-O.webp",
    url: "https://www.mercadolivre.com.br/samsung-galaxy-s24-ultra-5g-512gb-titnio/p/MLB33678310"
  }
];

// ============================================================================
// FUNÇÕES DE GERAÇÃO AUTOMÁTICA
// ============================================================================

async function generateSitemap(products) {
  const now = new Date().toISOString().split('T')[0];
  let xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${CONFIG.siteUrl}</loc>
    <lastmod>${now}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>`;

  products.forEach(p => {
    const slug = p.name.toLowerCase().replace(/[^\w ]+/g, '').replace(/ +/g, '-');
    xml += `
  <url>
    <loc>${CONFIG.siteUrl}#produto-${p.id}</loc>
    <lastmod>${now}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>`;
  });

  xml += '\n</urlset>';
  await fs.writeFile(CONFIG.sitemapPath, xml);
  console.log('✅ Sitemap gerado com sucesso!');
}

async function generateRobots() {
  const content = `User-agent: *
Allow: /

Sitemap: ${CONFIG.siteUrl}sitemap.xml`;
  await fs.writeFile(CONFIG.robotsPath, content);
  console.log('✅ Robots.txt gerado com sucesso!');
}

async function processImage(url, id) {
  try {
    const fileName = `${id}.webp`;
    const dest = path.join(CONFIG.imageDir, fileName);
    await fs.ensureDir(CONFIG.imageDir);

    const response = await axios({
      url,
      responseType: 'arraybuffer',
      timeout: 10000
    });

    await sharp(response.data)
      .resize(500, 500, { fit: 'inside' })
      .webp({ quality: 80 })
      .toFile(dest);

    return `images/produtos/${fileName}`;
  } catch (err) {
    return url;
  }
}

// ============================================================================
// EXECUÇÃO
// ============================================================================

async function run() {
  console.log('🚀 Iniciando Robô com Geração de SEO...');
  
  const finalProducts = [];

  for (let p of fallbackOffers) {
    console.log(`Processando: ${p.name}`);
    
    // Aplicar Desconto
    p.discount = Math.round(((p.originalPrice - p.price) / p.originalPrice) * 100);

    // Aplicar Links de Afiliado
    if (p.store === 'mercadolivre') {
      p.url = `https://www.mercadolivre.com.br/social/${CONFIG.affiliates.mercadolivre}?item=${p.id}`;
    } else {
      const sep = p.url.includes('?') ? '&' : '?';
      p.url = `${p.url}${sep}tag=${CONFIG.affiliates.amazon}`;
    }

    // Processar Imagem
    p.image = await processImage(p.image, p.id);
    
    finalProducts.push(p);
  }

  // Salvar Produtos
  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, finalProducts, { spaces: 2 });

  // Gerar SEO
  await generateSitemap(finalProducts);
  await generateRobots();

  console.log(`✨ FIM: ${finalProducts.length} produtos publicados com SEO!`);
}

run();
