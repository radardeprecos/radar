/**
 * RADAR DE PREÇOS — Versão Ultra Rápida
 */

const API_URL = 'data/products/offers.json?v=' + Date.now(); // Cache bust

async function loadOffers() {
    try {
        const res = await fetch(API_URL);
        const data = await res.json();
        
        const grid = document.getElementById('featuredGrid');
        if (grid && data.length > 0) {
            grid.innerHTML = data.map(p => `
                <div class="product-card">
                    <div class="product-badge">↓ ${p.discount}%</div>
                    <div class="store-badge ${p.store}">${p.store}</div>
                    <div class="card-image">
                        <img src="${p.image}" alt="${p.name}" onerror="this.src='assets/images/placeholder.svg'">
                    </div>
                    <div class="card-content">
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
        
        // Stats
        const stat = document.getElementById('statTotal');
        if (stat) stat.innerText = data.length + '+';
        
    } catch (e) {
        console.error('Erro ao carregar ofertas:', e);
    }
}

document.addEventListener('DOMContentLoaded', loadOffers);
// Tentar carregar novamente após 1s se falhar
setTimeout(loadOffers, 1000);
