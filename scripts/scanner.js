const puppeteer = require('puppeteer');
const fs = require('fs-extra');
const path = require('path');

/**
 * RADAR DE PREÇOS v7.0 — ESTABILIDADE TOTAL
 * URLs de Imagem Diretas (não quebram).
 * Links de Afiliados Sociais Corretos.
 */

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  sitemapPath: path.join(__dirname, '../sitemap.xml'),
  siteUrl: 'https://radardeprecos.github.io/radar/',
  mlSocialId: 'vendas0nline',
  queries: ['iPhone 15', 'PlayStation 5 Slim', 'Samsung Galaxy S24', 'Smart TV 4K', 'Air Fryer Mondial'],
  minDiscount: 5
};

async function run() {
  console.log('=== SCANNER v7.0 INICIADO ===');
  const browser = await puppeteer.launch({ 
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

  const allProducts = [];

  for (const query of CONFIG.queries) {
    try {
      console.log(`Buscando: ${query}`);
      await page.goto(`https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`, { waitUntil: 'networkidle2' });

      const products = await page.evaluate(() => {
        const items = [];
        document.querySelectorAll('.ui-search-result__wrapper').forEach((el, i) => {
          if (i >= 4) return;
          const title = el.querySelector('.ui-search-item__title')?.innerText;
          const priceStr = el.querySelector('.andes-money-amount__fraction')?.innerText.replace(/\./g, '');
          const oldPriceStr = el.querySelector('.ui-search-price__part--del .andes-money-amount__fraction')?.innerText.replace(/\./g, '');
          const link = el.querySelector('a.ui-search-link')?.href;
          
          // Pegar imagem de alta qualidade
          const imgTag = el.querySelector('img.ui-search-result-image__element') || el.querySelector('img.poly-component__picture');
          let img = imgTag?.src || imgTag?.getAttribute('data-src');

          if (title && priceStr && link && img) {
            // Limpar ID do link do Mercado Livre
            const match = link.match(/MLB-?(\d+)/);
            const id = match ? 'MLB' + match[1] : 'ml-' + Math.random().toString(36).substr(2, 5);

            items.push({
              id: id,
              name: title,
              price: parseFloat(priceStr),
              originalPrice: oldPriceStr ? parseFloat(oldPriceStr) : parseFloat(priceStr) * 1.15,
              url: link,
              image: img.replace(/-I\.jpg/, '-O.jpg') // Forçar alta qualidade
            });
          }
        });
        return items;
      });

      for (const p of products) {
        const discount = Math.round(((p.originalPrice - p.price) / p.originalPrice) * 100);
        p.discount = discount;
        p.store = 'mercadolivre';
        
        // LINK DE AFILIADO SOCIAL CORRETO
        p.url = `https://www.mercadolivre.com.br/social/${CONFIG.mlSocialId}?item=${p.id}`;
        
        allProducts.push(p);
        console.log(`✅ Adicionado: ${p.name}`);
      }

    } catch (err) {
      console.error(`Erro na busca: ${query}`, err.message);
    }
  }

  if (allProducts.length > 0) {
    await fs.writeJson(CONFIG.dataPath, allProducts, { spaces: 2 });
    console.log(`✨ Scanner concluído: ${allProducts.length} produtos.`);
  }

  await browser.close();
}

run();
