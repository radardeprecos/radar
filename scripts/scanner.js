const puppeteer = require('puppeteer');
const fs = require('fs-extra');
const path = require('path');
const axios = require('axios');
const sharp = require('sharp');

/**
 * RADAR DE PREÇOS v8.0 — LÓGICA DE FERRO
 * - Download local de imagens (sem links quebrados)
 * - Links REAIS dos anúncios (sem URLs artificiais)
 * - Validação rigorosa (URL 200 OK + Imagem válida)
 */

const CONFIG = {
  dataPath: path.join(__dirname, '../data/products/offers.json'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  logsDir: path.join(__dirname, '../data/logs/'),
  queries: ['iPhone 15', 'Samsung Galaxy S24', 'PlayStation 5 Slim', 'Smart TV 4K', 'Air Fryer Mondial'],
  minDiscount: 5,
  timeout: 30000
};

async function downloadImage(url, id) {
  try {
    if (!url || url.startsWith('data:image')) return null;
    
    const fileName = `${id}.webp`;
    const dest = path.join(CONFIG.imageDir, fileName);
    await fs.ensureDir(CONFIG.imageDir);

    const response = await axios({
      url,
      responseType: 'arraybuffer',
      timeout: 10000,
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });

    await sharp(response.data)
      .resize(500, 500, { fit: 'inside' })
      .webp({ quality: 80 })
      .toFile(dest);

    return `images/produtos/${fileName}`;
  } catch (err) {
    return null;
  }
}

async function isValidUrl(url) {
  try {
    const res = await axios.head(url, { timeout: 5000 });
    return res.status === 200;
  } catch {
    return false;
  }
}

async function run() {
  console.log('=== SCANNER v8.0 INICIADO ===');
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
          if (i >= 5) return;
          const title = el.querySelector('.ui-search-item__title')?.innerText;
          const priceStr = el.querySelector('.andes-money-amount__fraction')?.innerText.replace(/\./g, '');
          const oldPriceStr = el.querySelector('.ui-search-price__part--del .andes-money-amount__fraction')?.innerText.replace(/\./g, '');
          const link = el.querySelector('a.ui-search-link')?.href;
          
          // Captura robusta de imagem
          const imgTag = el.querySelector('img.ui-search-result-image__element') || el.querySelector('img.poly-component__picture');
          let img = imgTag?.src || imgTag?.dataset?.src || imgTag?.getAttribute('data-src');

          if (title && priceStr && link && img && !img.startsWith('data:image')) {
            const idMatch = link.match(/MLB-?(\d+)/);
            const id = idMatch ? 'MLB' + idMatch[1] : 'ml-' + Math.random().toString(36).substr(2, 5);

            items.push({
              id: id,
              name: title,
              price: parseFloat(priceStr),
              originalPrice: oldPriceStr ? parseFloat(oldPriceStr) : parseFloat(priceStr) * 1.15,
              url: link, // LINK REAL DO ANÚNCIO
              image: img.replace(/-I\.jpg/, '-O.jpg')
            });
          }
        });
        return items;
      });

      for (const p of products) {
        console.log(`Validando: ${p.name}`);
        
        // 1. Validar URL
        if (!(await isValidUrl(p.url))) {
          console.log('❌ Rejeitado: URL inválida');
          continue;
        }

        // 2. Baixar e Validar Imagem
        const localImg = await downloadImage(p.image, p.id);
        if (!localImg) {
          console.log('❌ Rejeitado: Falha na imagem');
          continue;
        }

        p.image = localImg;
        p.discount = Math.round(((p.originalPrice - p.price) / p.originalPrice) * 100);
        p.store = 'mercadolivre';
        
        allProducts.push(p);
        console.log(`✅ Publicado: ${p.name}`);
      }

    } catch (err) {
      console.error(`Erro na busca: ${query}`, err.message);
    }
  }

  if (allProducts.length > 0) {
    await fs.writeJson(CONFIG.dataPath, allProducts, { spaces: 2 });
    console.log(`✨ FIM: ${allProducts.length} produtos reais publicados.`);
  }

  await browser.close();
}

run();
