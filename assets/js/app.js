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
    let cleanUrl = url.split('?')[0].replace('undefined', '').replace(/\/$/, '');
    return `${cleanUrl}/?tag=${CONFIG.affiliateAmazon}`;
  }
  
  if (product.store === 'mercadolivre' || url.includes('mercadolivre')) {
    // CORREÇÃO: Usar o permalink direto do Mercado Livre
    try {
      const u = new URL(url.includes('http') ? url : 'https://' + url);
      const cleanUrl = u.origin + u.pathname;
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
  
  // CORREÇÃO: Sistema de imagem local com fallback robusto
  let imgPath = 'assets/images/placeholder.svg';
  if (product.image) {
    if (product.image.startsWith('assets/products/')) {
      // Se for caminho relativo salvo no JSON, garantimos que comece com ./ ou caminho absoluto do repo
      imgPath = product.image;
    } else {
      // Se ainda for URL externa, tentamos usar, mas o fallback cuidará se falhar
      imgPath = product.image;
    }
  }

  const card = el('div', 'product-card');
  card.innerHTML = `
    <div class="card-image-wrap">
      <img
        src="${imgPath}"
        alt="${product.name}"
        loading="lazy"
        onerror="this.onerror=null; this.src='assets/images/placeholder.svg';"
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
  let imgPath = 'assets/images/placeholder.svg';
  if (product.image) {
    imgPath = product.image;
  }

  const row = el('div', 'offer-row');
  row.innerHTML = `
    <div class="offer-product">
      <img
        src="${imgPath}"
        alt="${product.name}"
        class="offer-img"
        loading="lazy"
        onerror="this.onerror=null; this.src='assets/images/placeholder.svg';"
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
    let imgPath = 'assets/images/placeholder.svg';
    if (p.image) {
      imgPath = p.image;
    }

    const item = el('a', 'top-product-item');
    item.href = link;
    item.target = '_blank';
    item.rel = 'noopener sponsored';
    item.innerHTML = `
      <span class="top-rank">${i + 1}</span>
      <img src="${imgPath}" alt="${p.name}" class="top-img" loading="lazy" onerror="this.onerror=null; this.src='assets/images/placeholder.svg';" />
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
  if (el3) { 
    let imgPath = 'assets/images/placeholder.svg';
    if (product.image) {
      imgPath = product.image;
    }
    el3.src = imgPath; 
    el3.alt = product.name; 
    el3.onerror = function() { this.src='assets/images/placeholder.svg'; };
  }
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
      results.innerHTML = matches.map(p => {
        let imgPath = 'assets/images/placeholder.svg';
        if (p.image) {
          imgPath = p.image;
        }
        return `
          <a href="${buildAffiliateLink(p)}" class="search-result-item" target="_blank" rel="noopener sponsored">
            <img src="${imgPath}" class="search-result-img" alt="${p.name}" onerror="this.onerror=null; this.src='assets/images/placeholder.svg';" />
            <div>
              <div class="search-result-name">${p.name}</div>
              <div class="search-result-price">${formatPrice(p.price)}</div>
            </div>
          </a>
        `;
      }).join('') || '<p style="padding:16px;color:var(--text-muted);font-size:13px">Nenhum resultado encontrado.</p>';
      results.classList.toggle('active', matches.length > 0 || state.searchQuery.length > 1);
    }
  });

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && results && !results.contains(e.target)) {
      results.classList.remove('active');
    }
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

// ===== INITIALIZE =====
async function init() {
  const loading = document.getElementById('loadingOverlay');
  
  // Theme
  applyTheme(state.theme);
  $('#themeToggle')?.addEventListener('click', toggleTheme);
  
  // Load Data
  const success = await loadData();
  if (loading) loading.style.display = 'none';
  
  if (success) {
    renderHeroProduct(state.products[0]);
    renderProductsGrid(state.products, 'featuredGrid', 12);
    renderOffersTable(state.products, 'offersTableBody', 10);
    renderTopProducts(state.products);
    updateStats(state.products);
    renderHeroChart(state.products);
  }
  
  // Interactions
  initSearch();
  initBackToTop();
  initMobileMenu();
  
  // Category Navigation
  $$('.cat-nav a, .cat-card, .sidebar-cat-item').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const cat = el.dataset.cat || 'all';
      setCategory(cat);
      window.scrollTo({ top: $('#featuredGrid').offsetTop - 150, behavior: 'smooth' });
    });
  });
}

async function loadData() {
  try {
    const res = await fetch(CONFIG.dataUrl + '?v=' + Date.now());
    const data = await res.json();
    state.products = Array.isArray(data) ? data : (data.products || []);
    state.filtered = [...state.products];
    return true;
  } catch (err) {
    console.error('Erro ao carregar dados:', err);
    return false;
  }
}

function updateStats(products) {
  const totalEl = document.getElementById('statTotal');
  if (totalEl) totalEl.textContent = products.length.toLocaleString('pt-BR') + '+';
}

function initBackToTop() {
  const btn = document.getElementById('backToTop');
  if (!btn) return;
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

function initMobileMenu() {
  const toggle = document.getElementById('menuToggle');
  const menu = document.getElementById('mobileMenu');
  if (!toggle || !menu) return;
  toggle.addEventListener('click', () => {
    menu.classList.toggle('open');
    toggle.textContent = menu.classList.contains('open') ? '✕' : '☰';
  });
}

function renderHeroChart(products) {
  const svg = document.getElementById('heroChartSvg');
  if (!svg || !products.length) return;
  const product = products[0];
  if (!product || !product.priceHistory || product.priceHistory.length < 2) return;
  const prices = product.priceHistory.map(h => h.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = max - min || 1;
  const w = 280, h = 100;
  const pts = prices.map((p, i) => {
    const x = (i / (prices.length - 1)) * w;
    const y = h - ((p - min) / range) * (h - 20) - 10;
    return `${x},${y}`;
  }).join(' ');
  svg.innerHTML = `<polyline points="${pts}" fill="none" stroke="#00c853" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="${w}" cy="${h - ((prices[prices.length-1] - min) / range) * (h - 20) - 10}" r="5" fill="#00c853"/>`;
}

document.addEventListener('DOMContentLoaded', init);
