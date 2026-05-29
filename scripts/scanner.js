/**
 * RADAR DE PREÇOS — Robô Scanner
 * Busca produtos, detecta preços, salva histórico e gera JSON para o site.
 */

const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');

// ===== CONFIG =====
const CONFIG = {
  affiliateAmazon: 'radar041-20',
  affiliateML: 'https://www.mercadolivre.com.br/social/vendas0nline',
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  historyDir: path.join(__dirname, '../data/history/'),
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

// ===== SCRAPERS =====

async function scrapeAmazon(query, category) {
  const products = [];
  try {
    const url = `https://www.amazon.com.br/s?k=${encodeURIComponent(query)}`;
    const { data } = await axios.get(url, {
      headers: { 'User-Agent': CONFIG.userAgent }
    });
    const $ = cheerio.load(data);

    $('.s-result-item[data-component-type="s-search-result"]').each((i, el) => {
      if (i >= 5) return; // Limite por query para evitar bloqueio

      const name = $(el).find('h2 span').text().trim();
      const priceWhole = $(el).find('.a-price-whole').text().replace(/[.,]/g, '').trim();
      const priceFraction = $(el).find('.a-price-fraction').text().trim();
      const price = parseFloat(`${priceWhole}.${priceFraction}`);
      
      const originalPriceText = $(el).find('.a-text-price span.a-offscreen').text().replace(/[R$\s.]/g, '').replace(',', '.').trim();
      const originalPrice = originalPriceText ? parseFloat(originalPriceText) : null;
      
      const image = $(el).find('.s-image').attr('src');
      const rawLink = $(el).find('h2 a').attr('href');
      
      if (name && price && rawLink) {
        const link = rawLink.startsWith('http') ? rawLink : 'https://www.amazon.com.br' + rawLink;
        products.push({
          id: 'amz-' + slugify(name.substring(0, 20) + '-' + price),
          name,
          price,
          originalPrice,
          image,
          url: link,
          store: 'amazon',
          category,
          timestamp: new Date().toISOString()
        });
      }
    });
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

    // Busca expandida para Mercado Livre
    const items = $('.ui-search-layout__item, .ui-search-result__wrapper');
    items.each((i, el) => {
      if (i >= 8) return; // Aumentado limite para pegar mais ofertas

      const name = $(el).find('.ui-search-item__title, .ui-search-result__content-title').text().trim();
      
      // Lógica de preço mais robusta
      const priceContainer = $(el).find('.andes-money-amount--cents, .ui-search-price__second-line').first();
      const priceText = priceContainer.find('.andes-money-amount__fraction').text().replace(/\./g, '').trim();
      const priceCents = priceContainer.find('.andes-money-amount__cents').text().trim() || '00';
      const price = parseFloat(`${priceText}.${priceCents}`);

      // Preço original para cálculo de desconto
      const originalPriceContainer = $(el).find('.andes-money-amount--previous, .ui-search-price__part--metadata');
      const originalPriceText = originalPriceContainer.find('.andes-money-amount__fraction').text().replace(/\./g, '').trim();
      const originalPrice = originalPriceText ? parseFloat(originalPriceText) : null;

      const image = $(el).find('.ui-search-result-image__element').attr('data-src') || 
                    $(el).find('.ui-search-result-image__element').attr('src') ||
                    $(el).find('img').attr('data-src');
      
      const link = $(el).find('a.ui-search-link, a.ui-search-result__content').attr('href');

      if (name && price) {
        products.push({
          id: 'ml-' + slugify(name.substring(0, 20) + '-' + price),
          name,
          price,
          originalPrice,
          image,
          url: link,
          store: 'mercadolivre',
          category,
          timestamp: new Date().toISOString()
        });
      }
    });
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

    // Adicionar novo preço ao histórico se for diferente do último
    const lastPrice = history.length > 0 ? history[history.length - 1].price : null;
    if (p.price !== lastPrice) {
      history.push({ price: p.price, date: p.timestamp });
      // Manter apenas os últimos 30 registros
      if (history.length > 30) history.shift();
      await fs.ensureDir(CONFIG.historyDir);
      await fs.writeJson(historyFile, history);
    }

    // Calcular métricas
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

    // Atualizar no DB principal
    const idx = db.findIndex(item => item.id === p.id);
    if (idx >= 0) {
      db[idx] = p;
    } else {
      db.push(p);
    }
  }

  // Ordenar por desconto e limitar a 100 produtos no JSON principal para performance
  db.sort((a, b) => (b.discount || 0) - (a.discount || 0));
  const finalDb = db.slice(0, 100);

  await fs.ensureDir(path.dirname(CONFIG.dataPath));
  await fs.writeJson(CONFIG.dataPath, finalDb, { spaces: 2 });
  console.log(`Processados ${newProducts.length} produtos. Banco de dados atualizado com ${finalDb.length} itens.`);
}

// ===== MAIN =====

async function run() {
  console.log('🚀 Iniciando Scanner Radar de Preços...');
  const allNewProducts = [];

  for (const cat of CONFIG.categories) {
    console.log(`\n📂 Categoria: ${cat.name}`);
    for (const query of cat.queries) {
      console.log(`🔍 Buscando: ${query}...`);
      
      const amz = await scrapeAmazon(query, cat.name);
      await delay(2000); // Delay amigável
      
      const ml = await scrapeMercadoLivre(query, cat.name);
      await delay(2000);

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
