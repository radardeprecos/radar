const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs-extra');
const path = require('path');
const sharp = require('sharp');

const CONFIG = {
  imageDir: path.join(__dirname, '../assets/products/'),
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};

async function cacheImage(url, id) {
  if (!url) return null;
  const fileName = `${id}.webp`;
  const filePath = path.join(CONFIG.imageDir, fileName);
  const publicPath = `assets/products/${fileName}`;
  try {
    await fs.ensureDir(CONFIG.imageDir);
    const response = await axios({
      url,
      method: 'GET',
      responseType: 'arraybuffer',
      timeout: 15000,
      headers: { 'User-Agent': CONFIG.userAgent }
    });
    await sharp(response.data).webp().toFile(filePath);
    return publicPath;
  } catch (err) {
    return null;
  }
}

async function test() {
  const query = 'playstation 5';
  const url = `https://lista.mercadolivre.com.br/${encodeURIComponent(query)}`;
  console.log(`🔍 Buscando ML: ${url}`);
  const { data } = await axios.get(url, { headers: { 'User-Agent': CONFIG.userAgent } });
  const $ = cheerio.load(data);
  
  // Novos seletores mais genéricos para o ML
  const items = $('.ui-search-result__wrapper, .ui-search-layout__item');
  console.log(`Encontrados ${items.length} itens.`);

  items.each(async (i, el) => {
    if (i >= 3) return;
    const name = $(el).find('h2').text().trim() || $(el).find('.ui-search-item__title').text().trim();
    const link = $(el).find('a').attr('href');
    const imageSrc = $(el).find('img').attr('data-src') || $(el).find('img').attr('src');
    
    console.log(`\n[${i}] Produto: ${name}`);
    console.log(`Link: ${link ? link.split('?')[0] : 'N/A'}`);
    console.log(`Imagem Original: ${imageSrc}`);
    
    if (imageSrc && name) {
        const local = await cacheImage(imageSrc, `test-${i}`);
        console.log(`Imagem Local: ${local}`);
    }
  });
}

test();
