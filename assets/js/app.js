/**
 * RADAR DE PREÇOS — Frontend App (Bypass Version)
 */

const API_URL = 'data/products/offers.json';

// Forçar remoção do loading após 3 segundos mesmo se falhar
setTimeout(hideLoading, 3000);

async function init() {
    console.log('Iniciando Radar...');
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Erro ao buscar dados');
        const products = await response.json();
        
        renderUI(products);
        hideLoading();
    } catch (err) {
        console.error('Falha no carregamento:', err);
        hideLoading();
        // Fallback: mostrar mensagem de erro amigável
        const grid = document.getElementById('featuredGrid');
        if (grid) grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding:50px;">Nenhuma oferta encontrada no momento.</div>';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.style.display = 'none', 500);
    }
}

function renderUI(products) {
    if (!products || products.length === 0) return;

    // Atualizar stats
    const statTotal = document.getElementById('statTotal');
    if (statTotal) statTotal.innerText = `${products.length}+`;

    // Featured Grid
    const featuredGrid = document.getElementById('featuredGrid');
    if (featuredGrid) {
        featuredGrid.innerHTML = products.map(p => `
            <div class="product-card">
                <div class="product-badge">↓ ${p.discount}%</div>
                <div class="store-badge ${p.store}">${p.store === 'mercadolivre' ? 'Mercado Livre' : 'Amazon'}</div>
                <div class="card-image">
                    <img src="${p.image}" alt="${p.name}" onerror="this.src='assets/images/placeholder.svg'">
                </div>
                <div class="card-content">
                    <span class="category">${p.category}</span>
                    <h3>${p.name}</h3>
                    <div class="price-box">
                        <div class="current-price">R$ ${p.price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                        <div class="price-details">
                            <span class="old-price">R$ ${p.originalPrice.toLocaleString('pt-BR')}</span>
                            <span class="lowest-price">Menor: R$ ${p.price.toLocaleString('pt-BR')}</span>
                        </div>
                    </div>
                    <a href="${p.url}" class="btn-offer" target="_blank">🛒 Ver oferta</a>
                </div>
            </div>
        `).join('');
    }

    // Hero Product
    const hero = products[0];
    const heroImg = document.getElementById('heroProductImg');
    if (heroImg) heroImg.src = hero.image;
    const heroName = document.getElementById('heroProductName');
    if (heroName) heroName.innerText = hero.name;
    const heroPrice = document.getElementById('heroProductPrice');
    if (heroPrice) heroPrice.innerText = `R$ ${hero.price.toLocaleString('pt-BR')}`;
}

document.addEventListener('DOMContentLoaded', init);
window.onload = hideLoading; // Garantia extra
