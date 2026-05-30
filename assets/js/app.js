/**
 * RADAR DE PREÇOS — Sistema de Renderização Definitivo
 */

const API_URL = 'data/products/offers.json?t=' + new Date().getTime();

async function init() {
    console.log('Iniciando Radar...');
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Erro na rede');
        const products = await response.json();
        
        if (!products || products.length === 0) {
            console.warn('Nenhum produto encontrado no JSON');
            return;
        }

        renderAll(products);
    } catch (err) {
        console.error('Erro crítico:', err);
    }
}

function renderAll(products) {
    // 1. Grid Principal (Featured)
    const featuredGrid = document.getElementById('featuredGrid');
    if (featuredGrid) {
        featuredGrid.innerHTML = products.map(p => `
            <div class="product-card">
                <div class="product-badge">↓ ${p.discount}%</div>
                <div class="store-badge ${p.store}">${p.store}</div>
                <div class="card-image">
                    <img src="${p.image}" alt="${p.name}" onerror="this.src='assets/images/placeholder.svg'">
                </div>
                <div class="card-content">
                    <span class="category">${p.category}</span>
                    <h3>${p.name}</h3>
                    <div class="price-box">
                        <div class="current-price">R$ ${p.price.toLocaleString('pt-BR')}</div>
                        <div class="price-details">
                            <span class="old-price">R$ ${p.originalPrice.toLocaleString('pt-BR')}</span>
                        </div>
                    </div>
                    <a href="${p.url}" class="btn-offer" target="_blank">🛒 Ver oferta</a>
                </div>
            </div>
        `).join('');
    }

    // 2. Tabela de Ofertas (Corrigindo ID)
    const tableBody = document.getElementById('offersTableBody');
    if (tableBody) {
        tableBody.innerHTML = products.map(p => `
            <div class="offer-row">
                <div class="offer-info">
                    <img src="${p.image}" alt="${p.name}" class="offer-thumb" onerror="this.src='assets/images/placeholder.svg'">
                    <span class="offer-title">${p.name}</span>
                </div>
                <div class="offer-price">R$ ${p.price.toLocaleString('pt-BR')}</div>
                <div class="offer-discount">${p.discount}%</div>
                <div class="offer-action">
                    <a href="${p.url}" class="btn-table" target="_blank">Ver</a>
                </div>
            </div>
        `).join('');
    }

    // 3. Sidebar (Top Products)
    const topProducts = document.getElementById('topProducts');
    if (topProducts) {
        topProducts.innerHTML = products.slice(0, 5).map((p, i) => `
            <a href="${p.url}" class="top-product-item" target="_blank">
                <div class="top-product-rank">${i + 1}</div>
                <div class="top-product-info">
                    <div class="top-product-name">${p.name}</div>
                    <div class="top-product-price">R$ ${p.price.toLocaleString('pt-BR')}</div>
                </div>
            </a>
        `).join('');
    }

    // 4. Hero Section
    const hero = products[0];
    const hImg = document.getElementById('heroProductImg');
    const hName = document.getElementById('heroProductName');
    const hPrice = document.getElementById('heroProductPrice');
    if (hImg) hImg.src = hero.image;
    if (hName) hName.innerText = hero.name;
    if (hPrice) hPrice.innerText = `R$ ${hero.price.toLocaleString('pt-BR')}`;

    // 5. Stats
    const stat = document.getElementById('statTotal');
    if (stat) stat.innerText = products.length + '+';
}

document.addEventListener('DOMContentLoaded', init);
// Garantia de execução
if (document.readyState === 'complete') init();
