(() => {
    'use strict';

    const countElements = {
        atendimento: document.getElementById('evaluation-service-count'),
        pratos: document.getElementById('evaluation-dishes-count'),
        estabelecimento: document.getElementById('evaluation-establishment-count')
    };
    const status = document.getElementById('evaluation-live-status');

    async function updateEvaluationCounts() {
        try {
            const response = await fetch('/api/avaliacoes/', { cache: 'no-store' });
            if (!response.ok) {
                throw new Error('Não foi possível atualizar o painel de avaliações.');
            }
            const counts = await response.json();
            Object.entries(countElements).forEach(([category, element]) => {
                if (element && Number.isInteger(counts[category])) {
                    element.textContent = String(counts[category]);
                }
            });
            status.textContent = `Atualizado às ${new Date().toLocaleTimeString('pt-BR')}. Atualização automática a cada 5 segundos.`;
            status.classList.remove('is-error');
        } catch (error) {
            status.textContent = `${error.message} Tentaremos novamente em 5 segundos.`;
            status.classList.add('is-error');
        }
    }

    updateEvaluationCounts();
    window.setInterval(updateEvaluationCounts, 5000);
})();
