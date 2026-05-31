
// Radar de Preços - Script Principal Profissional

const isSubDir = window.location.pathname.includes('/categorias/') || window.location.pathname.includes('/ofertas/') || window.location.pathname.includes('/sobre/') || window.location.pathname.includes('/contato/') || window.location.pathname.includes('/privacidade/') || window.location.pathname.includes('/termos/') || window.location.pathname.includes('/quem-somos/');
const DATA_URL = isSubDir ? '../../data/products/offers.json' : 'data/products/offers.json';
let allProducts = [];
let currentSlide = 0;
let carouselInterval;

// --- Utilitários ---
function formatPrice(value) {
  return parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

function safeAffiliateUrl(product) {
  const aff = product.custom_affiliate_url || '';
  if (aff && !aff.includes('/social/') && !aff.includes('vendas0nline?')) {
    return aff;
  }
  return product.permalink || product.url || '';
}

// --- Deduplicação de Produtos ---
function deduplicateProducts(products) {
  const originalCount = products.length;
  const uniqueMap = new Map();
  
  products.forEach(p => {
    // Chave primária: ID. Secundária: Permalink. Terciária: Nome + Preço.
    const key = p.id || p.permalink || `${p.name}_${p.price}`;
    if (!uniqueMap.has(key)) {
      uniqueMap.set(key, p);
    } else {
      // Se já existe, mantém o que tiver maior desconto
      const existing = uniqueMap.get(key);
      if ((p.custom_discount_pct || 0) > (existing.custom_discount_pct || 0)) {
        uniqueMap.set(key, p);
      }
    }
  });
  
  const finalProducts = Array.from(uniqueMap.values());
  console.log(`[Deduplicação] Original: ${originalCount} | Final: ${finalProducts.length} | Removidos: ${originalCount - finalProducts.length}`);
  return finalProducts;
}

// --- Histórico de Preços Local ---
function updatePriceHistory(product) {
  const history = JSON.parse(localStorage.getItem('price_history') || '{}');
  const pid = product.id;
  const currentPrice = parseFloat(product.price);
  
  if (!history[pid]) {
    history[pid] = { min: currentPrice, last: currentPrice };
    localStorage.setItem('price_history', JSON.stringify(history));
    return false;
  } else {
    const isMin = currentPrice <= history[pid].min;
    if (isMin) history[pid].min = currentPrice;
    history[pid].last = currentPrice;
    localStorage.setItem('price_history', JSON.stringify(history));
    return isMin;
  }
}

// --- Lógica de Selos Dinâmicos ---
function getBadges(product, isTopDiscount, isHistoricalMin) {
  let badges = [];
  const discount = product.custom_discount_pct || 0;
  const price = parseFloat(product.price);

  if (isTopDiscount) badges.push('<span class="badge badge-promo-dia">🔥 Promoção do Dia</span>');
  if (isHistoricalMin) badges.push('<span class="badge badge-historico">🏅 Melhor Preço da História</span>');
  
  if (discount >= 50) {
    badges.push('<span class="badge badge-baixou">📉 Preço Baixou</span>');
  } else if (price > 1000) {
    badges.push('<span class="badge badge-premium">👑 Oferta Premium</span>');
  } else if (discount >= 30) {
    badges.push('<span class="badge badge-custo-beneficio">🏆 Custo-Benefício</span>');
  }

  if (badges.length === 0) {
    if (product.id && product.id.charCodeAt(0) % 3 === 0) badges.push('<span class="badge badge-mais-vendido">🚀 Mais Vendido</span>');
    else if (product.id && product.id.charCodeAt(0) % 2 === 0) badges.push('<span class="badge badge-recomendado">⭐ Recomendado</span>');
  }

  return badges.join('');
}

// --- Renderização do Carrossel ---
function renderCarousel(products) {
  const container = document.getElementById('heroProduct');
  if (!container) return;

  // Carrossel já recebe produtos deduplicados. Pegamos os top 8.
  const carouselProducts = products.slice(0, 8);
  
  let slidesHtml = carouselProducts.map((p, idx) => {
    const isFirst = idx === 0;
    const badgeHtml = isFirst ? '<span class="badge badge-promo-dia" style="position:static; display:inline-block; margin-bottom:10px;">🔥 OFERTA IMPERDÍVEL</span>' : '';
    
    return `
      <div class="carousel-slide ${isFirst ? 'featured' : ''}">
        <div class="carousel-info">
          ${badgeHtml}
          <h2>${escapeHtml(p.name)}</h2>
          <p>Aproveite esta oferta selecionada com ${p.custom_discount_pct}% de desconto!</p>
          <div class="price-tag">R$ ${formatPrice(p.price)} <span class="old-price">R$ ${formatPrice(p.originalPrice)}</span></div>
          <a href="${escapeHtml(safeAffiliateUrl(p))}" class="btn" target="_blank">🛒 Ver Oferta no Mercado Livre</a>
        </div>
        <div class="carousel-img">
          <img src="${escapeHtml(p.image || p.thumbnail)}" alt="${escapeHtml(p.name)}" loading="lazy">
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="carousel-container">
      <div class="carousel-track" id="carouselTrack">${slidesHtml}</div>
      <div class="carousel-nav">
        <button class="carousel-btn" id="prevBtn">❮</button>
        <button class="carousel-btn" id="nextBtn">❯</button>
      </div>
      <div class="carousel-indicators" id="carouselIndicators">
        ${carouselProducts.map((_, i) => `<div class="indicator ${i === 0 ? 'active' : ''}" data-index="${i}"></div>`).join('')}
      </div>
    </div>
  `;

  setupCarouselLogic(carouselProducts.length);
}

function setupCarouselLogic(count) {
  const track = document.getElementById('carouselTrack');
  const indicators = document.querySelectorAll('.indicator');
  if (!track) return;
  
  function goToSlide(n) {
    currentSlide = (n + count) % count;
    track.style.transform = `translateX(-${currentSlide * 100}%)`;
    indicators.forEach((ind, i) => ind.classList.toggle('active', i === currentSlide));
  }

  document.getElementById('nextBtn')?.addEventListener('click', () => goToSlide(currentSlide + 1));
  document.getElementById('prevBtn')?.addEventListener('click', () => goToSlide(currentSlide - 1));
  
  indicators.forEach(ind => {
    ind.addEventListener('click', () => goToSlide(parseInt(ind.dataset.index)));
  });

  if (carouselInterval) clearInterval(carouselInterval);
  carouselInterval = setInterval(() => goToSlide(currentSlide + 1), 5000);
}

// --- Renderização do Grid ---
function renderGrid(products, excludeFromCarousel = []) {
  const grid = document.getElementById('featuredGrid');
  if (!grid) return;

  // Filtrar produtos que já estão no carrossel para não repetir no grid
  const carouselIds = new Set(excludeFromCarousel.map(p => p.id));
  const gridProducts = products.filter(p => !carouselIds.has(p.id)).slice(0, 24);

  grid.innerHTML = gridProducts.map((p, idx) => {
    const isHistMin = updatePriceHistory(p);
    const badges = getBadges(p, idx === 0, isHistMin);
    
    return `
      <div class="product-card">
        <span class="badge discount-badge">↓ ${p.custom_discount_pct}% OFF</span>
        ${badges}
        <div class="card-img">
          <img src="${escapeHtml(p.image || p.thumbnail)}" alt="${escapeHtml(p.name)}" loading="lazy">
        </div>
        <h3>${escapeHtml(p.name).substring(0, 60)}...</h3>
        <div class="price-tag">R$ ${formatPrice(p.price)}</div>
        <a href="${escapeHtml(safeAffiliateUrl(p))}" class="btn" target="_blank" style="width:100%">Ver Oferta</a>
      </div>
    `;
  }).join('');
}

// --- Seção de Notícias ---
function renderNews() {
  const main = document.querySelector('main');
  if (!main || document.getElementById('newsSection')) return;

  const newsData = [
    { title: "Como economizar no Mercado Livre em 2026", summary: "Dicas essenciais para encontrar os melhores cupons e ofertas relâmpago.", img: "https://images.unsplash.com/photo-1556742044-3c52d6e88c62?w=400" },
    { title: "Review: Os melhores celulares custo-benefício", summary: "Analisamos os modelos que dominam o mercado este mês.", img: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400" },
    { title: "Guia de Compras: Eletrodomésticos Inteligentes", summary: "Transforme sua casa com tecnologia sem gastar uma fortuna.", img: "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=400" }
  ];

  const newsHtml = `
    <section class="news-section" id="newsSection">
      <div class="section-header"><h2>📰 Novas Postagens</h2></div>
      <div class="news-carousel">
        <div class="news-track" id="newsTrack">
          ${newsData.map(n => `
            <div class="news-slide">
              <div class="news-img"><img src="${n.img}" alt="${n.title}" loading="lazy"></div>
              <div class="news-info">
                <h3>${n.title}</h3>
                <p>${n.summary}</p>
                <a href="#" class="btn" style="padding: 8px 20px; font-size: 14px; margin-top:0">Ler Mais</a>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </section>
  `;

  const gridSection = document.querySelector('.section');
  if (gridSection) {
    gridSection.insertAdjacentHTML('beforebegin', newsHtml);
  }

  let newsIndex = 0;
  setInterval(() => {
    const track = document.getElementById('newsTrack');
    if (track) {
      newsIndex = (newsIndex + 1) % newsData.length;
      track.style.transform = `translateY(-${newsIndex * 200}px)`;
    }
  }, 6000);
}

// --- Inicialização ---
async function init() {
  try {
    const res = await fetch(DATA_URL + '?t=' + Date.now());
    let rawProducts = await res.json();
    
    // 1. Deduplicação Global
    allProducts = deduplicateProducts(rawProducts);
    
    // 2. Ordenar por desconto para o carrossel
    const sorted = [...allProducts].sort((a, b) => (b.custom_discount_pct || 0) - (a.custom_discount_pct || 0));
    const carouselItems = sorted.slice(0, 8);
    
    // 3. Renderizar componentes
    renderCarousel(sorted);
    renderGrid(allProducts, carouselItems); // Passa os itens do carrossel para excluir do grid
    renderNews();
    
    setupCategoryFilters();
    setupSearch();
  } catch (e) {
    console.error('Erro ao carregar ofertas:', e);
  }
}

function setupCategoryFilters() {
  const tabs = document.querySelectorAll('.cat-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const category = tab.getAttribute('data-cat');
      if (category === 'todos') {
        renderGrid(allProducts);
      } else {
        const filtered = allProducts.filter(p => p.custom_category_slug === category);
        renderGrid(filtered);
      }
    });
  });
}

function setupSearch() {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      if (query.length === 0) {
        renderGrid(allProducts);
      } else {
        const filtered = allProducts.filter(p => 
          (p.name || '').toLowerCase().includes(query) ||
          (p.custom_category_slug || '').toLowerCase().includes(query)
        );
        renderGrid(filtered);
      }
    });
  }
}

// Theme Toggle
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  themeToggle.innerText = savedTheme === 'dark' ? '☀️' : '🌙';
  themeToggle.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeToggle.innerText = isDark ? '🌙' : '☀️';
  });
}

// Iniciar
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
