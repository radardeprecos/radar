/**
 * RADAR DE PREÇOS — Robô Scanner (Versão Otimizada com Cache WebP)
 * Busca produtos, detecta preços, salva histórico e gera JSON para o site.
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

  // Se já existe, não baixa de novo para economizar banda/tempo
  if (await fs.exists(filePath)) {
    return publicPath;
  }

  try {
    await fs.ensureDir(CONFIG.imageDir);
    const response = await axios({
      url,
      method: 'GET',
      responseType: 'arraybuffer',
      timeout: 10000,
      headers: { 'User-Agent': CONFIG.userAgent }
    });

    await sharp(response.data)
      .resize(400, 400, { fit: 'inside', withoutEnlargement: true })
      .webp({ quality: 80 })
      .toFile(filePath);

    return publicPath;
  } catch (err) {
    console.error(`❌ Erro ao cachear imagem (${id}):`, err.message);
    return null; // Fallback será tratado no frontend
  }
}

// ===== SCRAPERS =====

async function scrapeAmazon(query, category) {
  const products = [];
  try {
    const url = `https://www.amazon.com.br/s?k=${encodeURIComponent(query)}`;
    const { data } = await axios.get(url, {
      headers: { 'User-Agent': CONFIG.userAgent }
    });
    const $ = cheerio.load(data);

    const items = $('.s-result-item[data-component-type="s-search-result"]');
    for (let i = 0; i < items.length; i++) {
      if (i >= 12) break;
      const el = items[i];

      const name = $(el).find('h2 span').text().trim();
      const priceWhole = $(el).find('.a-price-whole').text().replace(/[.,]/g, '').trim();
      const priceFraction = $(el).find('.a-price-fraction').text().trim();
      const price = parseFloat(`${priceWhole}.${priceFraction}`);
      
      const originalPriceText = $(el).find('.a-text-price span.a-offscreen').text().replace(/[R$\s.]/g, '').replace(',', '.').trim();
      const originalPrice = originalPriceText ? parseFloat(originalPriceText) : null;
      
      const imageSrc = $(el).find('.s-image').attr('src');
      const rawLink = $(el).find('h2 a').attr('href');
      
      if (name && price && rawLink && rawLink !== 'undefined') {
        const asinMatch = rawLink.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/);
        const asin = asinMatch ? asinMatch[1] : null;
        
        let link = rawLink;
        if (asin) {
            link = `https://www.amazon.com.br/dp/${asin}`;
        } else if (!link.startsWith('http')) {
            link = 'https://www.amazon.com.br' + (link.startsWith('/') ? '' : '/') + link;
        }
        link = link.split('?')[0];
        
        const id = 'amz-' + slugify(name.substring(0, 20) + '-' + price);
        const localImage = await cacheImage(imageSrc, id);

        products.push({
          id,
          name,
          price,
          originalPrice,
          image: localImage || imageSrc,
          url: link,
          store: 'amazon',
          category,
          timestamp: new Date().toISOString()
        });
      }
    }
  } catch (err) {
    console.error(`Erro Amazon (${query}):`, err.message);
  }
  return products;
}

async function scrapeMercadoLivre(query, category) {
  const products = [];
  try {
    const url = `https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`;
    const { data } = await axios.get(url, {
      headers: { 'User-Agent': CONFIG.userAgent }
    });
    const $ = cheerio.load(data);

    const items = $('.ui-search-layout__item, .ui-search-result__wrapper');
    for (let i = 0; i < items.length; i++) {
      if (i >= 15) break;
      const el = items[i];

      const name = $(el).find('.ui-search-item__title, .ui-search-result__content-title').text().trim();
      
      const priceContainer = $(el).find('.andes-money-amount--cents, .ui-search-price__second-line').first();
      const priceText = priceContainer.find('.andes-money-amount__fraction').text().replace(/\./g, '').trim();
      const priceCents = priceContainer.find('.andes-money-amount__cents').text().trim() || '00';
      const price = parseFloat(`${priceText}.${priceCents}`);

      const originalPriceContainer = $(el).find('.andes-money-amount--previous, .ui-search-price__part--metadata');
      const originalPriceText = originalPriceContainer.find('.andes-money-amount__fraction').text().replace(/\./g, '').trim();
      const originalPrice = originalPriceText ? parseFloat(originalPriceText) : null;

      const imageSrc = $(el).find('.ui-search-result-image__element').attr('data-src') || 
                       $(el).find('.ui-search-result-image__element').attr('src') ||
                       $(el).find('img').attr('data-src');
      
      // CORREÇÃO: Usar o permalink direto se disponível no atributo ou no link principal
      let link = $(el).find('a.ui-search-link, a.ui-search-result__content').attr('href');
      if (link) {
          link = link.split('#')[0].split('?')[0]; // Limpa rastreadores
      }

      if (name && price) {
        const id = 'ml-' + slugify(name.substring(0, 20) + '-' + price);
        const localImage = await cacheImage(imageSrc, id);

        products.push({
          id,
          name,
          price,
          originalPrice,
          image: localImage || imageSrc,
          url: link,
          store: 'mercadolivre',
          category,
          timestamp: new Date().toISOString()
        });
      }
    }
  } catch (err) {
    console.error(`Erro ML (${query}):`, err.message);
  }
  return products;
}

// ===== DATA PROCESSING =====

async function processProducts(newProducts) {
  let db = [];
  if (await fs.exists(CONFIG.dataPath)) {
    db = await fs.readJson(CONFIG.dataPath);
  }

  for (const p of newProducts) {
    const historyFile = path.join(CONFIG.historyDir, `${p.id}.json`);
    let history = [];
    
    if (await fs.exists(historyFile)) {
      history = await fs.readJson(historyFile);
    }

    const lastPrice = history.length > 0 ? history[history.length - 1].price : null;
    if (p.price !== lastPrice) {
      history.push({ price: p.price, date: p.timestamp });
      if (history.length > 30) history.shift();
      await fs.ensureDir(CONFIG.historyDir);
      await fs.writeJson(historyFile, history);
    }

    const prices = history.map(h => h.price);
    const lowestPrice = Math.min(...prices);
    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
    
    p.lowestPrice = lowestPrice;
    p.avgPrice = parseFloat(avgPrice.toFixed(2));
    p.isLowestPrice = p.price <= lowestPrice;
    p.priceHistory = history;
    p.discount = p.originalPrice ? Math.round(((p.originalPrice - p.price) / p.originalPrice) * 100) : 0;
    p.priceDrop = lastPrice ? Math.round(((lastPrice - p.price) / lastPrice) * 100) : 0;
    p.isFlash = p.discount >= 30;

    const idx = db.findIndex(item => item.id === p.id);
    if (idx >= 0) {
      db[idx] = p;
    } else {
      db.push(p);
    }
  }

  db.sort((a, b) => (b.discount || 0) - (a.discount || 0));
  const finalDb = db.slice(0, 100);

  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, finalDb, { spaces: 2 });
  
  await generateSitemap(finalDb);
  
  console.log(`Processados ${newProducts.length} produtos. Banco de dados atualizado com ${finalDb.length} itens.`);
}

async function generateSitemap(products) {
  const baseUrl = 'https://radardeprecos.github.io/radar';
  let xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n`;
  
  xml += `  <url>\n    <loc>${baseUrl}/</loc>\n    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>\n    <changefreq>hourly</changefreq>\n    <priority>1.0</priority>\n  </url>\n`;
  
  const categories = [...new Set(products.map(p => p.category))];
  for (const cat of categories) {
    xml += `  <url>\n    <loc>${baseUrl}/?cat=${encodeURIComponent(cat.toLowerCase())}</loc>\n    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n`;
  }

  for (const p of products) {
    xml += `  <url>\n    <loc>${baseUrl}/p/${p.id}.html</loc>\n    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.6</priority>\n  </url>\n`;
    await generateProductPage(p);
  }
  
  xml += `</urlset>`;
  await fs.writeFile(path.join(__dirname, '../sitemap.xml'), xml);
}

async function generateProductPage(p) {
  const pDir = path.join(__dirname, '../p');
  await fs.ensureDir(pDir);
  
  const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${p.name} - Menor Preço no Radar</title>
    <meta name="description" content="Oferta de ${p.name} por apenas R$ ${p.price}. Confira o menor preço da história no Radar de Preços!">
    <meta http-equiv="refresh" content="2;url=../index.html?id=${p.id}">
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: #0f172a; color: white; text-align: center; }
        .loader { border: 4px solid #1e293b; border-top: 4px solid #00c853; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="loader"></div>
    <h1>Redirecionando para a oferta...</h1>
    <p>Estamos te levando para o menor preço de <strong>${p.name}</strong></p>
    <script>window.location.href = '../index.html?id=${p.id}';</script>
</body>
</html>`;

  await fs.writeFile(path.join(pDir, `${p.id}.html`), html);
}

// ===== MAIN =====

async function run() {
  console.log('🚀 Iniciando Scanner Radar de Preços (com Cache de Imagens)...');
  const allNewProducts = [];

  for (const cat of CONFIG.categories) {
    console.log(`\n📂 Categoria: ${cat.name}`);
    for (const query of cat.queries) {
      console.log(`🔍 Buscando: ${query}...`);
      
      const amz = await scrapeAmazon(query, cat.name);
      await delay(1000); 
      
      const ml = await scrapeMercadoLivre(query, cat.name);
      await delay(1000);

      allNewProducts.push(...amz, ...ml);
    }
  }

  if (allNewProducts.length > 0) {
    await processProducts(allNewProducts);
  } else {
    console.log('⚠️ Nenhum produto encontrado nesta rodada.');
  }

  console.log('\n✅ Scanner finalizado com sucesso!');
}

run().catch(err => {
  console.error('❌ Erro fatal no scanner:', err);
  process.exit(1);
});
