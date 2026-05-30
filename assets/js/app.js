/**
 * RADAR DE PREÇOS — Frontend App
 * Gerenciamento de UI e renderização de ofertas.
 */

const API_URL = 'data/products/offers.json';

async function init() {
    try {
        const response = await fetch(API_URL);
        const products = await response.json();
        
        renderUI(products);
        hideLoading();
    } catch (err) {
        console.error('Erro ao carregar ofertas:', err);
        // Mesmo em erro, removemos o loading para não travar o usuário
        hideLoading();
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function renderUI(products) {
    if (!products || products.length === 0) return;

    // 1. Atualizar Estatísticas
    const statTotal = document.getElementById('statTotal');
    if (statTotal) statTotal.innerText = `${products.length}+`;

    // 2. Atualizar Hero (primeiro produto)
    const hero = products[0];
    const heroImg = document.getElementById('heroProductImg');
    const heroName = document.getElementById('heroProductName');
    const heroPrice = document.getElementById('heroProductPrice');

    if (heroImg) heroImg.src = hero.image;
    if (heroName) heroName.innerText = hero.name;
    if (heroPrice) heroPrice.innerText = `R$ ${hero.price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;

    // 3. Renderizar Grid de Destaques (Featured)
    const featuredGrid = document.getElementById('featuredGrid');
    if (featuredGrid) {
        featuredGrid.innerHTML = products.slice(0, 10).map(p => createProductCard(p)).join('');
    }

    // 4. Renderizar Tabela de Ofertas
    const tableBody = document.getElementById('offersTableBody');
    if (tableBody) {
        tableBody.innerHTML = products.map(p => createTableRow(p)).join('');
    }
}

function createProductCard(p) {
    const discountBadge = p.discount ? `<div class="product-badge">↓ ${p.discount}%</div>` : '';
    const storeBadge = `<div class="store-badge ${p.store}">${p.store === 'amazon' ? '🔥 Amazon' : '🔥 Mercado Livre'}</div>`;
    
    return `
        <div class="product-card">
            ${discountBadge}
            ${storeBadge}
            <div class="card-image">
                <img src="${p.image}" alt="${p.name}" onerror="this.src='assets/images/placeholder.svg'">
            </div>
            <div class="card-content">
                <span class="category">${p.category}</span>
                <h3>${p.name}</h3>
                <div class="price-box">
                    <div class="current-price">R$ ${p.price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</div>
                    <div class="price-details">
                        ${p.originalPrice ? `<span class="old-price">R$ ${p.originalPrice.toLocaleString('pt-BR')}</span>` : ''}
                        <span class="lowest-price">Menor: R$ ${p.price.toLocaleString('pt-BR')}</span>
                    </div>
                </div>
                ${p.isLowestPrice ? '<div class="lowest-tag">🔥 Menor preço</div>' : ''}
                <a href="${p.url}" class="btn-offer" target="_blank" rel="noopener sponsored">🛒 Ver oferta</a>
            </div>
        </div>
    `;
}

function createTableRow(p) {
    return `
        <div class="offer-row">
            <div class="offer-info">
                <img src="${p.image}" alt="${p.name}" class="offer-thumb" onerror="this.src='assets/images/placeholder.svg'">
                <div class="offer-title-box">
                    <span class="offer-title">${p.name}</span>
                    <span class="offer-store">${p.store}</span>
                </div>
            </div>
            <div class="offer-price">R$ ${p.price.toLocaleString('pt-BR')}</div>
            <div class="offer-lowest">R$ ${p.price.toLocaleString('pt-BR')}</div>
            <div class="offer-discount">${p.discount || 0}%</div>
            <div class="offer-action">
                <a href="${p.url}" class="btn-table" target="_blank">Ver oferta</a>
            </div>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', init);
