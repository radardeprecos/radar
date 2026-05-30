const DATA_URL = 'data/products/offers.json';
let allProducts = [];

async function init() {
  try {
    const res = await fetch(DATA_URL + '?t=' + Date.now());
    allProducts = await res.json();
    render(allProducts);
    setupCategoryFilters();
  } catch (e) {
    console.error('Erro ao carregar ofertas:', e);
    const heroEl = document.getElementById('heroProduct');
    if (heroEl) {
      heroEl.innerHTML = '<p style="padding: 20px; text-align: center; color: #999;">Erro ao carregar ofertas. O robô está trabalhando!</p>';
    }
  }
}

function render(products) {
  if (products.length === 0) return;
  
  // Hero
  const hero = products[0];
  const heroEl = document.getElementById('heroProduct');
  if (heroEl) {
    heroEl.innerHTML = `
      <div class="hero-card">
        <div class="hero-img"><img src="${escapeHtml(hero.custom_image_url || hero.image || '')}" alt="${escapeHtml(hero.name || '')}"></div>
        <div class="hero-info">
          <span class="badge">↓ ${hero.custom_discount_pct || hero.discount || 0}%</span>
          <h1>${escapeHtml(hero.name || '')}</h1>
          <div class="price-tag">R$ ${formatPrice(hero.price || 0)} <span class="old-price">R$ ${formatPrice(hero.originalPrice || 0)}</span></div>
          <a href="${escapeHtml(hero.custom_affiliate_url || hero.url || '')}" class="btn" target="_blank" rel="noopener noreferrer">🛒 Ver oferta no Mercado Livre</a>
        </div>
      </div>
    `;
  }

  // Grid
  const grid = document.getElementById('featuredGrid');
  if (grid) {
    grid.innerHTML = products.slice(1, 13).map(p => `
      <div class="product-card">
        <span class="badge">↓ ${p.custom_discount_pct || p.discount || 0}%</span>
        <div class="card-img"><img src="${escapeHtml(p.custom_image_url || p.image || '')}" alt="${escapeHtml(p.name || '')}"></div>
        <h3>${escapeHtml((p.name || '').substring(0, 50))}${(p.name || '').length > 50 ? '...' : ''}</h3>
        <div class="price-tag" style="font-size: 20px;">R$ ${formatPrice(p.price || 0)}</div>
        <a href="${escapeHtml(p.custom_affiliate_url || p.url || '')}" class="btn" style="width: 100%; text-align: center;" target="_blank" rel="noopener noreferrer">Ver</a>
      </div>
    `).join('');
  }
}

function setupCategoryFilters() {
  const tabs = document.querySelectorAll('.cat-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const category = tab.getAttribute('data-cat');
      filterByCategory(category);
    });
  });
}

function filterByCategory(category) {
  if (category === 'todos') {
    render(allProducts);
  } else {
    const filtered = allProducts.filter(p => p.custom_category_slug === category);
    render(filtered);
  }
}

function formatPrice(value) {
  return parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Theme toggle
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

// Search functionality
const searchInput = document.getElementById('searchInput');
if (searchInput) {
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    if (query.length === 0) {
      render(allProducts);
    } else {
      const filtered = allProducts.filter(p => 
        (p.name || '').toLowerCase().includes(query) ||
        (p.custom_category_slug || '').toLowerCase().includes(query)
      );
      render(filtered);
    }
  });
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
