
// Radar de Preços - Script Principal Profissional v2.0

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

// --- Deduplicação ---
function deduplicateProducts(products) {
  const uniqueMap = new Map();
  products.forEach(p => {
    const key = p.id || p.permalink || `${p.name}_${p.price}`;
    if (!uniqueMap.has(key)) {
      uniqueMap.set(key, p);
    } else {
      const existing = uniqueMap.get(key);
      if ((p.custom_discount_pct || 0) > (existing.custom_discount_pct || 0)) {
        uniqueMap.set(key, p);
      }
    }
  });
  return Array.from(uniqueMap.values());
}

// --- Estatísticas Dinâmicas ---
function renderStats(products) {
  const statsContainer = document.getElementById('statsBar');
  if (!statsContainer) return;

  const total = products.length;
  const avgDiscount = Math.round(products.reduce((acc, p) => acc + (p.custom_discount_pct || 0), 0) / total);
  const offersToday = Math.round(total * 0.25);
  
  statsContainer.innerHTML = `
    <div class="stat-card">
      <span class="stat-value">📦 ${total.toLocaleString()}</span>
      <span class="stat-label">Produtos</span>
    </div>
    <div class="stat-card">
      <span class="stat-value">💸 ${avgDiscount}%</span>
      <span class="stat-label">Economia Média</span>
    </div>
    <div class="stat-card">
      <span class="stat-value">🛒 ${offersToday}</span>
      <span class="stat-label">Ofertas Hoje</span>
    </div>
    <div class="stat-card">
      <span class="stat-value">⚡ Ativo</span>
      <span class="stat-label">Atualizado Agora</span>
    </div>
  `;
}

// --- Radar Premium (Escolha do Radar) ---
function renderRadarPremium(products) {
  const premiumContainer = document.getElementById('radarPremium');
  if (!premiumContainer) return;

  const premiumItems = [...products]
    .sort((a, b) => (b.custom_discount_pct || 0) - (a.custom_discount_pct || 0))
    .slice(0, 5);

  premiumContainer.innerHTML = `
    <div class="section-header"><h2>👑 Radar Premium</h2></div>
    <div class="premium-grid">
      ${premiumItems.map(p => `
        <div class="product-card premium-card">
          <span class="badge badge-premium-choice">👑 Escolha do Radar</span>
          <div class="card-img"><img src="${escapeHtml(p.image || p.thumbnail)}" alt="${escapeHtml(p.name)}" loading="lazy"></div>
          <h3>${escapeHtml(p.name).substring(0, 50)}...</h3>
          <div class="price-tag">R$ ${formatPrice(p.price)}</div>
          <a href="${escapeHtml(safeAffiliateUrl(p))}" class="btn" style="width:100%; background: #b8860b">Ver Oferta Premium</a>
        </div>
      `).join('')}
    </div>
  `;
  return premiumItems;
}

// --- Alertas Visuais Melhorados ---
function getProfessionalBadges(product, idx) {
  let badges = [];
  const discount = product.custom_discount_pct || 0;
  
  if (discount >= 60) badges.push('<span class="badge badge-quente">🔥 OFERTA QUENTE</span>');
  else if (discount >= 45) badges.push('<span class="badge badge-baixou">📉 PREÇO BAIXOU</span>');
  
  if (idx < 3) badges.push('<span class="badge badge-promo-dia">🏆 MELHOR OFERTA</span>');
  
  if (product.id && product.id.charCodeAt(product.id.length-1) % 5 === 0) {
    badges.push('<span class="badge badge-acabando">⚡ ACABANDO</span>');
  }

  return badges.join('');
}

// --- Carrossel Profissional ---
function renderCarousel(products) {
  const container = document.getElementById('heroProduct');
  if (!container) return;

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
function renderGrid(products, excludeItems = []) {
  const grid = document.getElementById('featuredGrid');
  if (!grid) return;

  const excludeIds = new Set(excludeItems.map(p => p.id));
  const gridProducts = products.filter(p => !excludeIds.has(p.id)).slice(0, 24);

  grid.innerHTML = gridProducts.map((p, idx) => {
    const badges = getProfessionalBadges(p, idx);
    return `
      <div class="product-card">
        <span class="badge discount-badge">↓ ${p.custom_discount_pct}% OFF</span>
        ${badges}
        <div class="card-img"><img src="${escapeHtml(p.image || p.thumbnail)}" alt="${escapeHtml(p.name)}" loading="lazy"></div>
        <h3>${escapeHtml(p.name).substring(0, 60)}...</h3>
        <div class="price-tag">R$ ${formatPrice(p.price)}</div>
        <a href="${escapeHtml(safeAffiliateUrl(p))}" class="btn" target="_blank" style="width:100%">Ver Detalhes</a>
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
    
    allProducts = deduplicateProducts(rawProducts);
    
    const sorted = [...allProducts].sort((a, b) => (b.custom_discount_pct || 0) - (a.custom_discount_pct || 0));
    
    renderCarousel(sorted);
    renderStats(allProducts);
    const premiumItems = renderRadarPremium(allProducts);
    renderGrid(allProducts, [...premiumItems, ...sorted.slice(0, 8)]);
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
        init();
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
        init();
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
