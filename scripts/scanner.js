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
  historyDir: path.join(__dirname, '../data/history/'),
  logsDir: path.join(__dirname, '../data/logs/'),
  imageDir: path.join(__dirname, '../images/produtos/'),
  
  // IDs de Afiliado
  affiliates: {
    amazon: 'radar041-20',
    mercadolivre: 'vendas0nline'
  },
  
  // URLs Base
  urls: {
    amazon: 'https://www.amazon.com.br',
    mercadolivre: 'https://www.mercadolivre.com.br'
  },
  
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  
  // Critérios de Publicação
  minDiscount: 10,  // Desconto mínimo 10%
  priceHistoryDays: 30,
  
  // Timeouts
  timeout: 10000
};

// ============================================================================
// LOGGER
// ============================================================================

class Logger {
  constructor() {
    this.logs = [];
    this.timestamp = new Date().toISOString();
  }

  log(type, message, data = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      type,
      message,
      data
    };
    this.logs.push(entry);
    console.log(`[${type}] ${message}`, data);
  }

  info(msg, data) { this.log('INFO', msg, data); }
  success(msg, data) { this.log('SUCCESS', msg, data); }
  warn(msg, data) { this.log('WARN', msg, data); }
  error(msg, data) { this.log('ERROR', msg, data); }

  async save() {
    await fs.ensureDir(CONFIG.logsDir);
    const filename = `log-${new Date().toISOString().split('T')[0]}.json`;
    const filepath = path.join(CONFIG.logsDir, filename);
    await fs.writeJson(filepath, this.logs, { spaces: 2 });
  }
}

const logger = new Logger();

// ============================================================================
// VALIDAÇÃO DE PRODUTOS
// ============================================================================

class ProductValidator {
  static validate(product) {
    const errors = [];

    // Validar imagem
    if (!product.image || product.image.trim() === '') {
      errors.push('Imagem vazia');
    }

    // Validar título
    if (!product.name || product.name.trim().length < 5) {
      errors.push('Título inválido ou muito curto');
    }

    // Validar preço
    if (!product.price || product.price <= 0) {
      errors.push('Preço inválido');
    }

    // Validar preço anterior
    if (!product.originalPrice || product.originalPrice <= 0) {
      errors.push('Preço anterior inválido');
    }

    // Validar desconto
    if (!product.discount || product.discount < CONFIG.minDiscount) {
      errors.push(`Desconto menor que ${CONFIG.minDiscount}%`);
    }

    // Validar URL
    if (!product.url || !this.isValidUrl(product.url)) {
      errors.push('URL inválida ou quebrada');
    }

    // Validar categoria
    if (!product.category || product.category.trim() === '') {
      errors.push('Categoria vazia');
    }

    // Validar marketplace
    if (!product.store || !['amazon', 'mercadolivre'].includes(product.store)) {
      errors.push('Marketplace inválido');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  static isValidUrl(url) {
    try {
      new URL(url);
      return url.startsWith('http');
    } catch {
      return false;
    }
  }
}

// ============================================================================
// DOWNLOAD E PROCESSAMENTO DE IMAGENS
// ============================================================================

async function downloadAndProcessImage(imageUrl, productId) {
  try {
    if (!imageUrl || imageUrl.trim() === '') {
      logger.warn('Imagem vazia', { productId });
      return null;
    }

    const fileName = `${productId}.webp`;
    const dest = path.join(CONFIG.imageDir, fileName);
    await fs.ensureDir(CONFIG.imageDir);

    const response = await axios({
      url: imageUrl,
      responseType: 'arraybuffer',
      headers: { 'User-Agent': CONFIG.userAgent },
      timeout: CONFIG.timeout
    });

    if (!response.data || response.data.length === 0) {
      logger.warn('Resposta de imagem vazia', { productId, imageUrl });
      return null;
    }

    await sharp(response.data)
      .resize(500, 500, { fit: 'inside' })
      .webp({ quality: 80 })
      .toFile(dest);

    logger.success('Imagem processada', { productId, fileName });
    return `images/produtos/${fileName}`;
  } catch (err) {
    logger.error('Erro ao baixar imagem', { productId, error: err.message });
    return null;
  }
}

// ============================================================================
// COLETA DO MERCADO LIVRE
// ============================================================================

async function fetchMercadoLivre() {
  logger.info('Iniciando coleta Mercado Livre...');
  const products = [];

  try {
    // Buscar produtos em destaque (celulares, notebooks, etc)
    const categories = [
      { name: 'Celulares', url: 'https://www.mercadolivre.com.br/celulares-e-telefones' },
      { name: 'Notebooks', url: 'https://www.mercadolivre.com.br/informatica/notebooks' },
      { name: 'Eletrodomésticos', url: 'https://www.mercadolivre.com.br/eletrodomesticos' }
    ];

    for (const cat of categories) {
      try {
        const response = await axios({
          url: cat.url,
          headers: { 'User-Agent': CONFIG.userAgent },
          timeout: CONFIG.timeout
        });

        const $ = cheerio.load(response.data);
        const items = $('[data-item-id]').slice(0, 5); // Pegar top 5

        items.each((i, el) => {
          try {
            const $el = $(el);
            const title = $el.find('[class*="title"]').text().trim();
            const priceText = $el.find('[class*="price"]').text().trim();
            const imageUrl = $el.find('img').attr('src');
            const productUrl = $el.find('a').attr('href');

            if (title && priceText && imageUrl && productUrl) {
              const price = parseFloat(priceText.replace(/[^\d,]/g, '').replace(',', '.'));
              
              if (price > 0 && title.length > 5) {
                products.push({
                  id: `ml-${Date.now()}-${i}`,
                  name: title,
                  price,
                  originalPrice: price * 1.15, // Estimativa
                  discount: 10,
                  store: 'mercadolivre',
                  category: cat.name,
                  image: imageUrl,
                  url: productUrl,
                  source: 'ml-scrape'
                });
              }
            }
          } catch (e) {
            logger.warn('Erro ao parsear item ML', { error: e.message });
          }
        });
      } catch (err) {
        logger.error('Erro ao buscar categoria ML', { category: cat.name, error: err.message });
      }
    }

    logger.success(`Coleta ML concluída: ${products.length} produtos encontrados`);
  } catch (err) {
    logger.error('Erro geral na coleta ML', { error: err.message });
  }

  return products;
}

// ============================================================================
// COLETA DA AMAZON
// ============================================================================

async function fetchAmazon() {
  logger.info('Iniciando coleta Amazon...');
  const products = [];

  try {
    // Buscar produtos em destaque
    const searchTerms = [
      'iPhone 15',
      'Samsung Galaxy S24',
      'PlayStation 5',
      'Notebook Gamer',
      'Air Fryer'
    ];

    for (const term of searchTerms) {
      try {
        const searchUrl = `${CONFIG.urls.amazon}/s?k=${encodeURIComponent(term)}&tag=${CONFIG.affiliates.amazon}`;
        
        const response = await axios({
          url: searchUrl,
          headers: { 'User-Agent': CONFIG.userAgent },
          timeout: CONFIG.timeout
        });

        const $ = cheerio.load(response.data);
        const items = $('[data-component-type="s-search-result"]').slice(0, 3);

        items.each((i, el) => {
          try {
            const $el = $(el);
            const title = $el.find('h2 a span').text().trim();
            const priceText = $el.find('[class*="price"]').text().trim();
            const imageUrl = $el.find('img').attr('src');
            const productLink = $el.find('h2 a').attr('href');

            if (title && priceText && imageUrl && productLink) {
              const price = parseFloat(priceText.replace(/[^\d,]/g, '').replace(',', '.'));
              
              if (price > 0 && title.length > 5) {
                const productUrl = productLink.startsWith('http') 
                  ? productLink 
                  : `${CONFIG.urls.amazon}${productLink}`;

                products.push({
                  id: `amz-${Date.now()}-${i}`,
                  name: title,
                  price,
                  originalPrice: price * 1.2,
                  discount: 15,
                  store: 'amazon',
                  category: term,
                  image: imageUrl,
                  url: productUrl,
                  source: 'amz-scrape'
                });
              }
            }
          } catch (e) {
            logger.warn('Erro ao parsear item Amazon', { error: e.message });
          }
        });
      } catch (err) {
        logger.error('Erro ao buscar termo Amazon', { term, error: err.message });
      }
    }

    logger.success(`Coleta Amazon concluída: ${products.length} produtos encontrados`);
  } catch (err) {
    logger.error('Erro geral na coleta Amazon', { error: err.message });
  }

  return products;
}

// ============================================================================
// APLICAR LINKS DE AFILIADO
// ============================================================================

function applyAffiliateLinks(product) {
  if (product.store === 'amazon') {
    // Adicionar tag de afiliado na URL da Amazon
    const separator = product.url.includes('?') ? '&' : '?';
    product.url = `${product.url}${separator}tag=${CONFIG.affiliates.amazon}`;
  } else if (product.store === 'mercadolivre') {
    // Redirecionar através do link de afiliado
    product.url = `${CONFIG.urls.mercadolivre}/social/${CONFIG.affiliates.mercadolivre}?item=${product.id}`;
  }
  return product;
}

// ============================================================================
// SALVAR HISTÓRICO DE PREÇOS
// ============================================================================

async function saveProductHistory(product) {
  try {
    const historyFile = path.join(CONFIG.historyDir, `${product.id}.json`);
    await fs.ensureDir(CONFIG.historyDir);

    let history = [];
    if (await fs.pathExists(historyFile)) {
      history = await fs.readJson(historyFile);
    }

    history.push({
      date: new Date().toISOString(),
      price: product.price,
      originalPrice: product.originalPrice,
      discount: product.discount
    });

    // Manter apenas últimos 30 dias
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    history = history.filter(h => new Date(h.date) > thirtyDaysAgo);

    await fs.writeJson(historyFile, history, { spaces: 2 });
    logger.info('Histórico salvo', { productId: product.id });
  } catch (err) {
    logger.error('Erro ao salvar histórico', { productId: product.id, error: err.message });
  }
}

// ============================================================================
// EXECUTAR SCANNER
// ============================================================================

async function run() {
  console.log('\n' + '='.repeat(80));
  console.log('🤖 RADAR DE PREÇOS — SCANNER INICIADO');
  console.log('='.repeat(80) + '\n');

  const startTime = Date.now();
  let finalProducts = [];

  try {
    // 1. Coletar produtos
    logger.info('Iniciando coleta de produtos...');
    const mlProducts = await fetchMercadoLivre();
    const amzProducts = await fetchAmazon();
    const allProducts = [...mlProducts, ...amzProducts];

    logger.info(`Total de produtos coletados: ${allProducts.length}`);

    // 2. Processar e validar
    logger.info('Validando e processando produtos...');
    for (const product of allProducts) {
      try {
        // Validar
        const validation = ProductValidator.validate(product);
        if (!validation.isValid) {
          logger.warn('Produto rejeitado', { 
            productId: product.id, 
            errors: validation.errors 
          });
          continue;
        }

        // Baixar e processar imagem
        const localImage = await downloadAndProcessImage(product.image, product.id);
        if (!localImage) {
          logger.warn('Produto rejeitado (sem imagem)', { productId: product.id });
          continue;
        }

        product.image = localImage;

        // Aplicar links de afiliado
        product = applyAffiliateLinks(product);

        // Salvar histórico
        await saveProductHistory(product);

        finalProducts.push(product);
        logger.success('Produto publicado', { 
          productId: product.id, 
          name: product.name,
          price: product.price
        });
      } catch (err) {
        logger.error('Erro ao processar produto', { 
          productId: product.id, 
          error: err.message 
        });
      }
    }

    // 3. Salvar arquivo final
    await fs.ensureDir(path.dirname(CONFIG.dataPath));
    await fs.writeJson(CONFIG.dataPath, finalProducts, { spaces: 2 });

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    logger.success(`Scanner concluído em ${duration}s`, {
      totalPublished: finalProducts.length,
      totalCollected: allProducts.length
    });

    console.log('\n' + '='.repeat(80));
    console.log(`✅ SUCESSO: ${finalProducts.length} produtos publicados`);
    console.log(`⏱️  Tempo: ${duration}s`);
    console.log('='.repeat(80) + '\n');

  } catch (err) {
    logger.error('Erro crítico no scanner', { error: err.message, stack: err.stack });
    console.error('\n❌ ERRO CRÍTICO:', err.message);
  } finally {
    // Salvar logs
    await logger.save();
  }
}

// Executar
run().catch(err => {
  console.error('Erro não capturado:', err);
  process.exit(1);
});
