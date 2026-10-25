// HG Contabilidade - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('HG Contabilidade carregado');
    
    // Animações suaves nos cards
    const cards = document.querySelectorAll('.step');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Contador animado
    const counters = document.querySelectorAll('.step-count, .stat-number');
    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        let current = 0;
        const increment = target / 30;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, 30);
    });
});
