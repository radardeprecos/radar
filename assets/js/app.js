/**
 * RADAR DE PREÇOS — Sistema de Renderização v2.1
 * Renderiza produtos com histórico de preços, validação e links de afiliados
 */

const API_URL = 'data/products/offers.json?t=' + new Date().getTime();

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

async function init() {
  console.log('🚀 Iniciando Radar de Preços v2.1...');
  try {
    const response = await fetch(API_URL);
    if (!response.ok) throw new Error(`Erro HTTP ${response.status}`);
    
    const products = await response.json();
    
    if (!products || products.length === 0) {
      console.warn('⚠️ Nenhum produto encontrado');
      showEmptyState();
      return;
    }

    console.log(`✅ ${products.length} produtos carregados`);
    renderAll(products);
  } catch (err) {
    console.error('❌ Erro crítico:', err);
    showErrorState(err.message);
  }
}

// ============================================================================
// RENDERIZAÇÃO PRINCIPAL
// ============================================================================

function renderAll(products) {
  // 1. Hero Section
  renderHero(products[0]);

  // 2. Grid de Ofertas em Destaque
  renderFeaturedGrid(products);

  // 3. Tabela de Ofertas
  renderOffersTable(products);

  // 4. Top Produtos (Sidebar)
  renderTopProducts(products);

  // 5. Categorias
  renderCategories(products);

  // 6. Stats
  updateStats(products);
}

// ============================================================================
// HERO SECTION
// ============================================================================

function renderHero(product) {
  const hero = document.getElementById('heroSection');
  if (!hero) return;

  const discount = product.discount || 0;
  const savings = Math.round((product.originalPrice - product.price) * 100) / 100;
  const imageUrl = product.image.startsWith('http') ? product.image : product.image;

  hero.innerHTML = `
    <div class="hero-content">
      <div class="hero-text">
        <h1>Ofertas com<br><span class="highlight">menor preço da história!</span></h1>
        <p>Monitoramos milhares de produtos todos os dias e mostramos quando o preço atinge o seu menor valor já registrado.</p>
        <div class="hero-actions">
          <button class="btn btn-primary" onclick="document.getElementById('featuredGrid').scrollIntoView({behavior: 'smooth'})">
            🔥 Ver ofertas agora
          </button>
          <button class="btn btn-secondary" onclick="document.getElementById('alertas').scrollIntoView({behavior: 'smooth'})">
            🔔 Receber alertas
          </button>
        </div>
      </div>
      <div class="hero-product">
        <div class="hero-card">
          <div class="hero-badge">↓ ${discount}%</div>
          <div class="hero-image">
            <img src="${imageUrl}" alt="${product.name}" onerror="this.src='https://via.placeholder.com/500x500?text=Imagem+Indisponivel'">
          </div>
          <div class="hero-info">
            <h3>${product.name}</h3>
            <div class="hero-prices">
              <div class="hero-current">R$ ${formatPrice(product.price)}</div>
              <div class="hero-original">R$ ${formatPrice(product.originalPrice)}</div>
            </div>
            <div class="hero-savings">Economize R$ ${formatPrice(savings)}</div>
            <a href="${product.url}" class="btn btn-offer" target="_blank" rel="noopener">
              🛒 Ver oferta
            </a>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ============================================================================
// GRID DE OFERTAS
// ============================================================================

function renderFeaturedGrid(products) {
  const grid = document.getElementById('featuredGrid');
  if (!grid) return;

  grid.innerHTML = products.slice(0, 12).map(p => {
    const savings = Math.round((p.originalPrice - p.price) * 100) / 100;
    const imageUrl = p.image.startsWith('http') ? p.image : p.image;
    return `
      <div class="product-card" data-product-id="${p.id}">
        <div class="product-badge">↓ ${p.discount}%</div>
        <div class="store-badge ${p.store}">${p.store === 'amazon' ? '🟠 Amazon' : '🟡 Mercado Livre'}</div>
        <div class="card-image">
          <img src="${imageUrl}" alt="${p.name}" onerror="this.src='https://via.placeholder.com/500x500?text=Imagem+Indisponivel'">
        </div>
        <div class="card-content">
          <span class="category">${p.category}</span>
          <h3>${p.name}</h3>
          <div class="price-box">
            <div class="current-price">R$ ${formatPrice(p.price)}</div>
            <div class="price-details">
              <span class="old-price">R$ ${formatPrice(p.originalPrice)}</span>
              <span class="savings">Economize R$ ${formatPrice(savings)}</span>
            </div>
          </div>
          <a href="${p.url}" class="btn-offer" target="_blank" rel="noopener">
            🛒 Ver oferta
          </a>
        </div>
      </div>
    `;
  }).join('');
}

// ============================================================================
// TABELA DE OFERTAS
// ============================================================================

function renderOffersTable(products) {
  const tableBody = document.getElementById('offersTableBody');
  if (!tableBody) return;

  tableBody.innerHTML = products.slice(0, 15).map(p => `
    <div class="offer-row">
      <div class="offer-info">
        <img src="${p.image}" alt="${p.name}" class="offer-thumb" onerror="this.src='https://via.placeholder.com/100x100?text=N/A'">
        <div class="offer-details">
          <span class="offer-title">${p.name}</span>
          <span class="offer-category">${p.category}</span>
        </div>
      </div>
      <div class="offer-price">
        <div class="current">R$ ${formatPrice(p.price)}</div>
        <div class="original">R$ ${formatPrice(p.originalPrice)}</div>
      </div>
      <div class="offer-discount">↓ ${p.discount}%</div>
      <div class="offer-action">
        <a href="${p.url}" class="btn-table" target="_blank" rel="noopener">Ver oferta</a>
      </div>
    </div>
  `).join('');
}

// ============================================================================
// TOP PRODUTOS
// ============================================================================

function renderTopProducts(products) {
  const topProducts = document.getElementById('topProducts');
  if (!topProducts) return;

  topProducts.innerHTML = products.slice(0, 5).map((p, i) => `
    <a href="${p.url}" class="top-product-item" target="_blank" rel="noopener">
      <div class="top-product-rank">🏆 #${i + 1}</div>
      <div class="top-product-info">
        <div class="top-product-name">${p.name}</div>
        <div class="top-product-price">R$ ${formatPrice(p.price)}</div>
        <div class="top-product-discount">↓ ${p.discount}%</div>
      </div>
    </a>
  `).join('');
}

// ============================================================================
// CATEGORIAS
// ============================================================================

function renderCategories(products) {
  const categoriesContainer = document.getElementById('categoriesContainer');
  if (!categoriesContainer) return;

  const categories = {};
  products.forEach(p => {
    if (!categories[p.category]) categories[p.category] = [];
    categories[p.category].push(p);
  });

  categoriesContainer.innerHTML = Object.entries(categories).map(([cat, items]) => {
    const bestPrice = items.reduce((min, p) => p.price < min ? p.price : min, Infinity);
    const bestProduct = items.find(p => p.price === bestPrice);
    
    return `
      <div class="category-card">
        <div class="category-header">
          <h3>${cat}</h3>
          <span class="category-count">${items.length} produtos</span>
        </div>
        <div class="category-preview">
          <img src="${bestProduct.image}" alt="${bestProduct.name}" onerror="this.src='https://via.placeholder.com/300x300?text=N/A'">
        </div>
        <div class="category-best">
          <div class="best-label">Melhor preço</div>
          <div class="best-price">R$ ${formatPrice(bestPrice)}</div>
          <a href="${bestProduct.url}" class="btn-category" target="_blank" rel="noopener">Ver</a>
        </div>
      </div>
    `;
  }).join('');
}

// ============================================================================
// STATS
// ============================================================================

function updateStats(products) {
  const statTotal = document.getElementById('statTotal');
  if (statTotal) statTotal.innerText = products.length + '+';

  const statUpdate = document.getElementById('statUpdate');
  if (statUpdate) {
    const now = new Date();
    statUpdate.innerText = now.toLocaleString('pt-BR');
  }

  const statAvgDiscount = document.getElementById('statAvgDiscount');
  if (statAvgDiscount) {
    const avgDiscount = Math.round(
      products.reduce((sum, p) => sum + (p.discount || 0), 0) / products.length
    );
    statAvgDiscount.innerText = avgDiscount + '%';
  }
}

// ============================================================================
// UTILITÁRIOS
// ============================================================================

function formatPrice(price) {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price);
}

function showEmptyState() {
  const main = document.querySelector('main');
  if (main) {
    main.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <h2>Nenhuma oferta disponível</h2>
        <p>O robô está coletando produtos. Volte em alguns minutos.</p>
      </div>
    `;
  }
}

function showErrorState(message) {
  const main = document.querySelector('main');
  if (main) {
    main.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <h2>Erro ao carregar ofertas</h2>
        <p>${message}</p>
      </div>
    `;
  }
}

// ============================================================================
// TEMA ESCURO/CLARO
// ============================================================================

function setupTheme() {
  const themeToggle = document.getElementById('themeToggle');
  if (!themeToggle) return;

  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const savedTheme = localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light');

  document.documentElement.setAttribute('data-theme', savedTheme);

  themeToggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    themeToggle.innerText = next === 'dark' ? '☀️' : '🌙';
  });

  themeToggle.innerText = savedTheme === 'dark' ? '☀️' : '🌙';
}

// ============================================================================
// INICIALIZAÇÃO
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  setupTheme();
  init();
});
