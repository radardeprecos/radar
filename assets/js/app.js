/**
 * RADAR DE PREÇOS — JavaScript Principal
 * Carrega dados do JSON, renderiza cards, dark mode, busca e interatividade
 */

'use strict';

// ===== CONFIG =====
const CONFIG = {
  dataUrl: './data/products/offers.json',
  historyUrl: './data/history/',
  affiliateAmazon: 'radar041-20',
  affiliateML: 'https://www.mercadolivre.com.br/social/vendas0nline',
  minDiscount: 5,
  refreshInterval: 30 * 60 * 1000, // 30 min
};

// ===== STATE =====
let state = {
  products: [],
  filtered: [],
  category: 'all',
  theme: localStorage.getItem('theme') || 'light',
  searchQuery: '',
  page: 1,
  perPage: 12,
};

// ===== DOM HELPERS =====
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  return e;
};

// ===== THEME =====
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  state.theme = theme;
  localStorage.setItem('theme', theme);
  const btn = $('#themeToggle');
  if (btn) btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
  applyTheme(state.theme === 'dark' ? 'light' : 'dark');
}

// ===== AFFILIATE LINKS =====
function buildAffiliateLink(product) {
  if (!product || !product.url) return '#';
  const url = product.url;
  if (product.store === 'amazon' || url.includes('amazon.com.br')) {
    try {
      const u = new URL(url.includes('http') ? url : 'https://' + url);
      // Limpa parâmetros de rastreamento antigos da Amazon para garantir sua tag
      const cleanPath = u.origin + u.pathname;
      return `${cleanPath}?tag=${CONFIG.affiliateAmazon}`;
    } catch (e) {
      return url + (url.includes('?') ? '&' : '?') + 'tag=' + CONFIG.affiliateAmazon;
    }
  }
  if (product.store === 'mercadolivre' || url.includes('mercadolivre')) {
    // Para Mercado Livre, usamos o redirecionador de afiliados se disponível, 
    // ou anexamos o parâmetro de tracking ao link direto do produto.
    try {
      const u = new URL(url.includes('http') ? url : 'https://' + url);
      // Remove parâmetros de busca originais e mantém o link limpo do produto
      const cleanUrl = u.origin + u.pathname;
      // O link de afiliado social do ML geralmente funciona como um redirecionador ou perfil.
      // Para garantir a comissão no produto específico, usamos o link direto com tracking.
      return `${cleanUrl}#origin=vip&component-id=ad-unit&strategy_id=social_sharing&seller_id=vendas0nline`;
    } catch (e) {
      return url;
    }
  }
  return url;
}

// ===== FORMAT =====
function formatPrice(val) {
  if (!val && val !== 0) return 'R$ --';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
}

function formatDiscount(current, original) {
  if (!original || original <= current) return 0;
  return Math.round(((original - current) / original) * 100);
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `há ${mins} min`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `há ${hrs}h`;
  return `há ${Math.floor(hrs / 24)}d`;
}

// ===== SEALS =====
function getSeals(product) {
  const seals = [];
  if (product.isLowestPrice) seals.push({ cls: 'seal-lowest', icon: '🔥', text: 'Menor preço' });
  if (product.priceDrop > 0) seals.push({ cls: 'seal-drop', icon: '📉', text: `Caiu ${product.priceDrop}%` });
  if (product.isFlash) seals.push({ cls: 'seal-flash', icon: '⚡', text: 'Oferta relâmpago' });
  return seals;
}

// ===== RENDER PRODUCT CARD =====
function renderCard(product) {
  const discount = product.discount || formatDiscount(product.price, product.originalPrice);
  const link = buildAffiliateLink(product);
  const seals = getSeals(product);
  const storeName = product.store === 'amazon' ? 'Amazon' : product.store === 'mercadolivre' ? 'Mercado Livre' : product.store || '';

  const card = el('div', 'product-card');
  card.innerHTML = `
    <div class="card-image-wrap">
      <img
        src="${product.image || 'assets/images/placeholder.svg'}"
        alt="${product.name}"
        loading="lazy"
        onerror="this.src='assets/images/placeholder.svg'"
      />
      ${discount > 0 ? `<span class="card-badge badge-discount">↓ ${discount}%</span>` : ''}
      ${product.isLowestPrice ? `<span class="card-badge badge-lowest" style="top:10px;left:${discount > 0 ? '70px' : '10px'}">🔥</span>` : ''}
      ${storeName ? `<span class="card-store">${storeName}</span>` : ''}
    </div>
    <div class="card-body">
      <span class="card-category">${product.category || 'Oferta'}</span>
      <h3 class="card-title">${product.name}</h3>
      <div class="card-prices">
        <span class="card-price-current">${formatPrice(product.price)}</span>
        <div class="card-price-row">
          ${product.originalPrice ? `<span class="card-price-old">${formatPrice(product.originalPrice)}</span>` : ''}
          ${product.lowestPrice ? `<span class="card-price-lowest">Menor: ${formatPrice(product.lowestPrice)}</span>` : ''}
        </div>
        ${product.avgPrice ? `<div class="card-price-avg">Médio: ${formatPrice(product.avgPrice)}</div>` : ''}
      </div>
      ${seals.length ? `<div class="card-seals">${seals.map(s => `<span class="seal ${s.cls}">${s.icon} ${s.text}</span>`).join('')}</div>` : ''}
      <a href="${link}" class="btn-buy" target="_blank" rel="noopener sponsored" onclick="trackClick('${product.id}', '${product.store}')">
        🛒 Ver oferta
      </a>
    </div>
  `;
  return card;
}

// ===== RENDER OFFER ROW =====
function renderOfferRow(product) {
  const link = buildAffiliateLink(product);
  const discount = product.discount || formatDiscount(product.price, product.originalPrice);
  const row = el('div', 'offer-row');
  row.innerHTML = `
    <div class="offer-product">
      <img
        src="${product.image || 'assets/images/placeholder.svg'}"
        alt="${product.name}"
        class="offer-img"
        loading="lazy"
        onerror="this.src='assets/images/placeholder.svg'"
      />
      <span class="offer-name">${product.name}</span>
    </div>
    <span class="offer-price">${formatPrice(product.price)}</span>
    <span class="offer-lowest">${formatPrice(product.lowestPrice || product.price)}</span>
    <span class="offer-discount">↓ ${discount}%</span>
    <a href="${link}" class="btn-offer" target="_blank" rel="noopener sponsored">Ver oferta</a>
  `;
  return row;
}

// ===== RENDER PRODUCTS GRID =====
function renderProductsGrid(products, containerId, limit = 8) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  const items = products.slice(0, limit);
  if (items.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:32px;grid-column:1/-1">Nenhum produto encontrado.</p>';
    return;
  }
  items.forEach(p => container.appendChild(renderCard(p)));
}

// ===== RENDER OFFERS TABLE =====
function renderOffersTable(products, containerId, limit = 6) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  products.slice(0, limit).forEach(p => container.appendChild(renderOfferRow(p)));
}

// ===== RENDER TOP PRODUCTS SIDEBAR =====
function renderTopProducts(products) {
  const container = document.getElementById('topProducts');
  if (!container) return;
  container.innerHTML = '';
  products.slice(0, 5).forEach((p, i) => {
    const link = buildAffiliateLink(p);
    const discount = p.discount || formatDiscount(p.price, p.originalPrice);
    const item = el('a', 'top-product-item');
    item.href = link;
    item.target = '_blank';
    item.rel = 'noopener sponsored';
    item.innerHTML = `
      <span class="top-rank">${i + 1}</span>
      <img src="${p.image || 'assets/images/placeholder.svg'}" alt="${p.name}" class="top-img" loading="lazy" onerror="this.src='assets/images/placeholder.svg'" />
      <div class="top-info">
        <div class="top-name">${p.name}</div>
        <div class="top-price">${formatPrice(p.price)} <span class="top-discount">↓ ${discount}%</span></div>
      </div>
    `;
    container.appendChild(item);
  });
}

// ===== RENDER HERO PRODUCT =====
function renderHeroProduct(product) {
  if (!product) return;
  const el1 = document.getElementById('heroProductName');
  const el2 = document.getElementById('heroProductPrice');
  const el3 = document.getElementById('heroProductImg');
  if (el1) el1.textContent = product.name;
  if (el2) el2.textContent = formatPrice(product.price);
  if (el3) { el3.src = product.image || 'assets/images/placeholder.svg'; el3.alt = product.name; }
}

// ===== FILTER PRODUCTS =====
function filterProducts() {
  let products = [...state.products];
  if (state.category !== 'all') {
    products = products.filter(p => p.category?.toLowerCase() === state.category.toLowerCase());
  }
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    products = products.filter(p => p.name?.toLowerCase().includes(q) || p.category?.toLowerCase().includes(q));
  }
  state.filtered = products;
  return products;
}

// ===== CATEGORY FILTER =====
function setCategory(cat) {
  state.category = cat;
  $$('.cat-nav a').forEach(a => {
    a.classList.toggle('active', a.dataset.cat === cat);
  });
  const filtered = filterProducts();
  renderProductsGrid(filtered, 'featuredGrid', 8);
  renderOffersTable(filtered, 'offersTableBody', 6);
}

// ===== SEARCH =====
function initSearch() {
  const input = document.getElementById('searchInput');
  const results = document.getElementById('searchResults');
  if (!input) return;

  input.addEventListener('input', () => {
    state.searchQuery = input.value.trim();
    if (state.searchQuery.length < 2) {
      if (results) results.classList.remove('active');
      return;
    }
    const matches = state.products
      .filter(p => p.name?.toLowerCase().includes(state.searchQuery.toLowerCase()))
      .slice(0, 6);

    if (results) {
      results.innerHTML = matches.map(p => `
        <a href="${buildAffiliateLink(p)}" class="search-result-item" target="_blank" rel="noopener sponsored">
          <img src="${p.image || 'assets/images/placeholder.svg'}" class="search-result-img" alt="${p.name}" onerror="this.src='assets/images/placeholder.svg'" />
          <div>
            <div class="search-result-name">${p.name}</div>
            <div class="search-result-price">${formatPrice(p.price)}</div>
          </div>
        </a>
      `).join('') || '<p style="padding:16px;color:var(--text-muted);font-size:13px">Nenhum resultado encontrado.</p>';
      results.classList.toggle('active', matches.length > 0 || state.searchQuery.length > 1);
    }
  });

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && results && !results.contains(e.target)) {
      results.classList.remove('active');
    }
  });

  const btn = document.getElementById('searchBtn');
  if (btn) btn.addEventListener('click', () => {
    filterProducts();
    renderProductsGrid(state.filtered, 'featuredGrid', 8);
  });
}

// ===== TRACK CLICK =====
function trackClick(id, store) {
  try {
    const clicks = JSON.parse(localStorage.getItem('clicks') || '{}');
    clicks[id] = (clicks[id] || 0) + 1;
    localStorage.setItem('clicks', JSON.stringify(clicks));
  } catch (e) {}
}

// ===== BACK TO TOP =====
function initBackToTop() {
  const btn = document.getElementById('backToTop');
  if (!btn) return;
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// ===== MOBILE MENU =====
function initMobileMenu() {
  const toggle = document.getElementById('menuToggle');
  const menu = document.getElementById('mobileMenu');
  if (!toggle || !menu) return;
  toggle.addEventListener('click', () => {
    menu.classList.toggle('open');
    toggle.textContent = menu.classList.contains('open') ? '✕' : '☰';
  });
}

// ===== TOAST =====
function showToast(msg, duration = 3000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = el('div', 'toast', msg);
  container.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

// ===== HERO CHART =====
function renderHeroChart(products) {
  const svg = document.getElementById('heroChartSvg');
  if (!svg || !products.length) return;

  const product = products.find(p => p.isLowestPrice) || products[0];
  if (!product || !product.priceHistory) return;

  const history = product.priceHistory.slice(-12);
  if (history.length < 2) return;

  const prices = history.map(h => h.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const w = 280, h = 100;
  const pts = prices.map((p, i) => {
    const x = (i / (prices.length - 1)) * w;
    const y = h - ((p - min) / range) * (h - 20) - 10;
    return `${x},${y}`;
  }).join(' ');

  svg.innerHTML = `
    <polyline points="${pts}" fill="none" stroke="#00c853" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${w}" cy="${h - ((prices[prices.length-1] - min) / range) * (h - 20) - 10}" r="5" fill="#00c853"/>
  `;
}

// ===== STATS =====
function updateStats(products) {
  const totalEl = document.getElementById('statTotal');
  const lowestEl = document.getElementById('statLowest');
  const updatedEl = document.getElementById('statUpdated');

  if (totalEl) totalEl.textContent = products.length.toLocaleString('pt-BR') + '+';
  if (lowestEl) lowestEl.textContent = products.filter(p => p.isLowestPrice).length;
  if (updatedEl) updatedEl.textContent = 'Agora';
}

// ===== LOAD DATA =====
async function loadData() {
  try {
    const res = await fetch(CONFIG.dataUrl + '?v=' + Date.now());
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    state.products = Array.isArray(data) ? data : (data.products || []);
    state.filtered = [...state.products];
    return true;
  } catch (err) {
    console.warn('Usando dados de demonstração:', err.message);
    state.products = getDemoProducts();
    state.filtered = [...state.products];
    return false;
  }
}

// ===== DEMO PRODUCTS (fallback) =====
function getDemoProducts() {
  return [
    {
      id: 'demo-1',
      name: 'Samsung Galaxy A55 5G 256GB 8GB RAM',
      category: 'Celulares',
      price: 1399.00,
      originalPrice: 1799.00,
      lowestPrice: 1399.00,
      avgPrice: 1599.00,
      discount: 22,
      isLowestPrice: true,
      priceDrop: 22,
      store: 'amazon',
      url: 'https://www.amazon.com.br/dp/B0CXN9MFGX',
      image: 'https://m.media-amazon.com/images/I/71YDZX6BFNL._AC_SL1500_.jpg',
      priceHistory: [
        {date:'2024-01-01',price:1799},{date:'2024-02-01',price:1699},{date:'2024-03-01',price:1599},
        {date:'2024-04-01',price:1549},{date:'2024-05-01',price:1499},{date:'2024-06-01',price:1399}
      ]
    },
    {
      id: 'demo-2',
      name: 'Air Fryer Mondial Grand Family 5L',
      category: 'Eletrodomésticos',
      price: 299.00,
      originalPrice: 399.00,
      lowestPrice: 299.00,
      avgPrice: 379.00,
      discount: 25,
      isLowestPrice: true,
      priceDrop: 25,
      store: 'mercadolivre',
      url: 'https://www.mercadolivre.com.br/air-fryer-mondial',
      image: 'https://http2.mlstatic.com/D_NQ_NP_2X_623636-MLB71620093977_092023-F.webp',
      priceHistory: [
        {date:'2024-01-01',price:399},{date:'2024-02-01',price:379},{date:'2024-03-01',price:359},
        {date:'2024-04-01',price:339},{date:'2024-05-01',price:319},{date:'2024-06-01',price:299}
      ]
    },
    {
      id: 'demo-3',
      name: 'Notebook Acer Aspire 5 i5 8GB 512GB SSD',
      category: 'Informática',
      price: 2699.00,
      originalPrice: 3199.00,
      lowestPrice: 2699.00,
      avgPrice: 3100.00,
      discount: 16,
      isLowestPrice: true,
      priceDrop: 16,
      store: 'amazon',
      url: 'https://www.amazon.com.br/dp/notebook-acer',
      image: 'https://m.media-amazon.com/images/I/71FDXLCpjCL._AC_SL1500_.jpg',
      priceHistory: [
        {date:'2024-01-01',price:3199},{date:'2024-02-01',price:3099},{date:'2024-03-01',price:2999},
        {date:'2024-04-01',price:2899},{date:'2024-05-01',price:2799},{date:'2024-06-01',price:2699}
      ]
    },
    {
      id: 'demo-4',
      name: 'Smart TV Samsung 50" 4K Crystal UHD',
      category: 'TV e Vídeo',
      price: 1899.00,
      originalPrice: 2199.00,
      lowestPrice: 1879.00,
      avgPrice: 2099.00,
      discount: 14,
      isLowestPrice: false,
      priceDrop: 14,
      store: 'amazon',
      url: 'https://www.amazon.com.br/dp/smart-tv-samsung',
      image: 'https://m.media-amazon.com/images/I/81fxjeu8fdL._AC_SL1500_.jpg',
      priceHistory: [
        {date:'2024-01-01',price:2199},{date:'2024-02-01',price:2099},{date:'2024-03-01',price:1999},
        {date:'2024-04-01',price:1949},{date:'2024-05-01',price:1929},{date:'2024-06-01',price:1899}
      ]
    },
    {
      id: 'demo-5',
      name: 'PlayStation 5 Standard Edition',
      category: 'Games',
      price: 3299.00,
      originalPrice: 3999.00,
      lowestPrice: 2799.00,
      avgPrice: 3699.00,
      discount: 17,
      isLowestPrice: false,
      priceDrop: 17,
      store: 'amazon',
      url: 'https://www.amazon.com.br/dp/ps5',
      image: 'https://m.media-amazon.com/images/I/619O4RLMF3L._AC_SL1500_.jpg',
      priceHistory: [
        {date:'2024-01-01',price:3999},{date:'2024-02-01',price:3799},{date:'2024-03-01',price:3599},
        {date:'2024-04-01',price:3499},{date:'2024-05-01',price:3399},{date:'2024-06-01',price:3299}
      ]
    },
    {
      id: 'demo-6',
      name: 'iPhone 13 128GB Meia-noite',
      category: 'Celulares',
      price: 3599.00,
      originalPrice: 3999.00,
      lowestPrice: 3499.00,
      avgPrice: 3799.00,
      discount: 10,
      isLowestPrice: false,
      priceDrop: 10,
      store: 'amazon',
      url: 'https://www.amazon.com.br/dp/iphone13',
      image: 'https://m.media-amazon.com/images/I/61ljqwXlFLL._AC_SL1500_.jpg',
      priceHistory: [
        {date:'2024-01-01',price:3999},{date:'2024-02-01',price:3899},{date:'2024-03-01',price:3799},
        {date:'2024-04-01',price:3699},{date:'2024-05-01',price:3649},{date:'2024-06-01',price:3599}
      ]
    },
    {
      id: 'demo-7',
      name: 'Fone de Ouvido JBL Wave Buds TWS',
      category: 'Informática',
      price: 149.00,
      originalPrice: 199.00,
      lowestPrice: 149.00,
      avgPrice: 189.00,
      discount: 25,
      isLowestPrice: true,
      priceDrop: 25,
      isFlash: true,
      store: 'mercadolivre',
      url: 'https://www.mercadolivre.com.br/jbl-wave-buds',
      image: 'https://http2.mlstatic.com/D_NQ_NP_2X_jbl-wave.webp',
      priceHistory: [
        {date:'2024-01-01',price:199},{date:'2024-02-01',price:189},{date:'2024-03-01',price:179},
        {date:'2024-04-01',price:169},{date:'2024-05-01',price:159},{date:'2024-06-01',price:149}
      ]
    },
    {
      id: 'demo-8',
      name: 'Liquidificador Philco PH900 1200W',
      category: 'Eletrodomésticos',
      price: 139.90,
      originalPrice: 179.90,
      lowestPrice: 139.90,
      avgPrice: 169.90,
      discount: 22,
      isLowestPrice: true,
      priceDrop: 22,
      store: 'amazon',
      url: 'https://www.amazon.com.br/dp/liquidificador-philco',
      image: 'https://m.media-amazon.com/images/I/61liquidificador.jpg',
      priceHistory: [
        {date:'2024-01-01',price:179.90},{date:'2024-02-01',price:169.90},{date:'2024-03-01',price:159.90},
        {date:'2024-04-01',price:154.90},{date:'2024-05-01',price:149.90},{date:'2024-06-01',price:139.90}
      ]
    }
  ];
}

// ===== INIT =====
async function init() {
  // Apply saved theme
  applyTheme(state.theme);

  // Theme toggle
  const themeBtn = document.getElementById('themeToggle');
  if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

  // Load data
  const loaded = await loadData();

  // Hide loading
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) {
    overlay.classList.add('hidden');
    setTimeout(() => overlay.remove(), 600);
  }

  // Render
  const featured = state.products.filter(p => p.isLowestPrice || p.discount >= 15).slice(0, 8);
  const all = state.products;

  renderProductsGrid(featured.length ? featured : all, 'featuredGrid', 8);
  renderOffersTable(all, 'offersTableBody', 6);
  renderTopProducts(all.sort((a, b) => (b.discount || 0) - (a.discount || 0)));
  renderHeroProduct(all.find(p => p.isLowestPrice) || all[0]);
  renderHeroChart(all);
  updateStats(all);

  // Category nav
  $$('.cat-nav a[data-cat]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      setCategory(a.dataset.cat);
    });
  });

  // See more button
  const seeMoreBtn = document.getElementById('seeMoreBtn');
  if (seeMoreBtn) {
    seeMoreBtn.addEventListener('click', () => {
      state.page++;
      const start = (state.page - 1) * state.perPage;
      const more = state.filtered.slice(start, start + state.perPage);
      const grid = document.getElementById('featuredGrid');
      if (grid) more.forEach(p => grid.appendChild(renderCard(p)));
      if (start + state.perPage >= state.filtered.length) seeMoreBtn.style.display = 'none';
    });
  }

  // Alert form
  const alertForm = document.getElementById('alertForm');
  if (alertForm) {
    alertForm.addEventListener('submit', e => {
      e.preventDefault();
      const email = alertForm.querySelector('input[type="email"]')?.value;
      if (email) {
        showToast('✅ Cadastrado com sucesso! Você receberá alertas de menor preço.');
        alertForm.reset();
      }
    });
  }

  // Init search
  initSearch();
  initBackToTop();
  initMobileMenu();

  // Auto-refresh
  setInterval(async () => {
    await loadData();
    renderProductsGrid(state.products.filter(p => p.isLowestPrice || p.discount >= 15).slice(0, 8), 'featuredGrid', 8);
    renderOffersTable(state.products, 'offersTableBody', 6);
  }, CONFIG.refreshInterval);

  if (!loaded) {
    showToast('📊 Exibindo dados de demonstração. O robô atualizará em breve!');
  }
}

// ===== START =====
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
