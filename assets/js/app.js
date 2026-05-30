/**
 * RADAR DE PREÇOS — Frontend App
 * Renderização dinâmica de ofertas com suporte a imagens locais.
 */

const API_URL = 'data/products/offers.json';

async function loadOffers() {
    try {
        const response = await fetch(API_URL);
        const products = await response.json();
        renderProducts(products);
    } catch (err) {
        console.error('Erro ao carregar ofertas:', err);
    }
}

function renderProducts(products) {
    const container = document.getElementById('productsGrid');
    if (!container) return;
    container.innerHTML = '';

    products.forEach(p => {
        const card = document.createElement('div');
        card.className = 'product-card';
        
        // CORREÇÃO: Caminho da imagem local com fallback
        const imgPath = p.image || 'assets/images/placeholder.svg';
        
        card.innerHTML = `
            <div class="card-image">
                <img src="${imgPath}" alt="${p.name}" onerror="this.src='assets/images/placeholder.svg'">
            </div>
            <div class="card-content">
                <span class="category">${p.category}</span>
                <h3>${p.name}</h3>
                <div class="price-box">
                    <span class="current-price">R$ ${p.price.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</span>
                    ${p.isLowestPrice ? '<span class="badge">Menor Preço!</span>' : ''}
                </div>
                <a href="${p.url}" class="btn-offer" target="_blank" rel="noopener sponsored">Ver oferta</a>
            </div>
        `;
        container.appendChild(card);
    });
}

document.addEventListener('DOMContentLoaded', loadOffers);
