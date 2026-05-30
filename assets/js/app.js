const DATA_URL = 'data/products/offers.json';
let allProducts = [];

async function init() {
  try {
    const res = await fetch(DATA_URL + '?t=' + Date.now());
    allProducts = await res.json();
    render(allProducts);
  } catch (e) {
    document.getElementById('heroProduct').innerHTML = '<p>Erro ao carregar ofertas. O robô está trabalhando!</p>';
  }
}

function render(products) {
  if (products.length === 0) return;
  
  // Hero
  const hero = products[0];
  document.getElementById('heroProduct').innerHTML = `
    <div class="hero-card">
      <div class="hero-img"><img src="${hero.image}" alt="${hero.name}"></div>
      <div class="hero-info">
        <span class="badge">↓ ${hero.discount}%</span>
        <h1>${hero.name}</h1>
        <div class="price-tag">R$ ${hero.price.toLocaleString('pt-BR')}<span class="old-price">R$ ${hero.originalPrice.toLocaleString('pt-BR')}</span></div>
        <a href="${hero.url}" class="btn" target="_blank">🛒 Ver oferta no Mercado Livre</a>
      </div>
    </div>
  `;

  // Grid
  const grid = document.getElementById('featuredGrid');
  grid.innerHTML = products.slice(1, 13).map(p => `
    <div class="product-card">
      <span class="badge">↓ ${p.discount}%</span>
      <div class="card-img"><img src="${p.image}" alt="${p.name}"></div>
      <h3>${p.name.substring(0, 50)}...</h3>
      <div class="price-tag" style="font-size: 20px;">R$ ${p.price.toLocaleString('pt-BR')}</div>
      <a href="${p.url}" class="btn" style="width: 100%; text-align: center;" target="_blank">Ver</a>
    </div>
  `).join('');
}

document.getElementById('themeToggle').onclick = () => {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  document.getElementById('themeToggle').innerText = isDark ? '🌙' : '☀️';
};

init();
