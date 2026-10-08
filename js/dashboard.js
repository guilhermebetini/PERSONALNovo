(() => {
    'use strict';

    const countElements = {
        atendimento: document.getElementById('evaluation-service-count'),
        pratos: document.getElementById('evaluation-dishes-count'),
        estabelecimento: document.getElementById('evaluation-establishment-count')
    };
    const status = document.getElementById('evaluation-live-status');
    const latestReviews = document.getElementById('latest-reviews-list');
    const topDishes = document.getElementById('top-dishes-dashboard-list');

    function renderStars(container, rating) {
        container.replaceChildren();
        container.setAttribute('aria-label', `Nota ${rating} de 5`);
        for (let value = 1; value <= 5; value += 1) {
            const star = document.createElement('span');
            star.className = `material-symbols-outlined${value <= Math.round(rating) ? ' filled' : ''}`;
            star.textContent = 'star';
            container.append(star);
        }
    }

    function formatAge(value) {
        const timestamp = new Date(value).getTime();
        if (Number.isNaN(timestamp)) return '';
        const minutes = Math.max(0, Math.floor((Date.now() - timestamp) / 60000));
        if (minutes < 1) return 'agora';
        if (minutes < 60) return `${minutes} min`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} h`;
        return `${Math.floor(hours / 24)} d`;
    }

    function renderLatestReviews(reviews) {
        if (!latestReviews) return;
        latestReviews.replaceChildren();
        if (!reviews.length) {
            const empty = document.createElement('p');
            empty.className = 'dashboard-list-empty';
            empty.textContent = 'Ainda não há avaliações registradas.';
            latestReviews.append(empty);
            return;
        }

        reviews.slice(0, 3).forEach((review) => {
            const item = document.createElement('article');
            item.className = 'review-item';
            const info = document.createElement('div');
            info.className = 'review-info';
            const title = document.createElement('h4');
            title.textContent = review.categoria === 'pratos'
                ? (review.prato || 'Avaliação de prato')
                : `Avaliação de ${review.categoria_label.toLowerCase()}`;
            const comment = document.createElement('p');
            comment.textContent = review.comentario || 'Sem comentário';
            info.append(title, comment);

            const stars = document.createElement('div');
            stars.className = 'review-stars';
            renderStars(stars, review.nota);

            const time = document.createElement('time');
            time.className = 'review-time';
            time.dateTime = review.criada_em;
            time.textContent = formatAge(review.criada_em);
            item.append(info, stars, time);
            latestReviews.append(item);
        });
    }

    function renderTopDishes(dishes) {
        if (!topDishes) return;
        topDishes.replaceChildren();
        if (!dishes.length) {
            const empty = document.createElement('p');
            empty.className = 'dashboard-list-empty';
            empty.textContent = 'Ainda não há avaliações de pratos.';
            topDishes.append(empty);
            return;
        }

        dishes.slice(0, 4).forEach((dish) => {
            const item = document.createElement('article');
            item.className = 'product-item';
            const image = document.createElement('div');
            image.className = 'product-img';

            const info = document.createElement('div');
            info.className = 'product-info';
            const name = document.createElement('h4');
            name.textContent = dish.dish_name;
            const total = document.createElement('small');
            total.textContent = `${dish.total} ${dish.total === 1 ? 'avaliação' : 'avaliações'}`;
            info.append(name, total);

            const count = document.createElement('span');
            count.className = 'product-count';
            count.textContent = String(dish.total);

            const stars = document.createElement('div');
            stars.className = 'product-stars';
            renderStars(stars, dish.media);

            const average = document.createElement('span');
            average.className = 'product-rating';
            average.textContent = `${Number(dish.media).toFixed(1).replace('.', ',')}/5`;
            item.append(image, info, count, stars, average);
            topDishes.append(item);
        });
    }

    function updateRatingSummary(data) {
        const averageElement = document.getElementById('dashboard-average-rating');
        const totalElement = document.getElementById('dashboard-total-ratings');
        const average = data.media_geral;
        const validAverage = Number.isFinite(average);
        const distribution = data.distribuicao_notas || {};

        if (averageElement) {
            averageElement.textContent = validAverage
                ? average.toFixed(1).replace('.', ',')
                : '—';
        }
        if (totalElement) {
            totalElement.textContent = `${data.total} ${data.total === 1 ? 'avaliação' : 'avaliações'}`;
        }
        document.querySelectorAll('[data-average-star]').forEach((star) => {
            star.classList.toggle(
                'filled',
                validAverage && Number(star.dataset.averageStar) <= Math.round(average)
            );
        });
        document.querySelectorAll('[data-rating-count]').forEach((element) => {
            const rating = element.dataset.ratingCount;
            element.textContent = String(Object.values(distribution).reduce(
                (sum, category) => sum + Number(category[rating] || 0),
                0
            ));
        });
    }

    function updateCharts(data) {
        document.querySelectorAll('[data-chart-category]').forEach((chart) => {
            const ratings = data.distribuicao_notas?.[chart.dataset.chartCategory] || {};
            const maximum = Math.max(0, ...Object.values(ratings).map(Number));
            chart.querySelectorAll('[data-rating]').forEach((bar) => {
                const count = Number(ratings[bar.dataset.rating] || 0);
                bar.style.height = maximum ? `${Math.max(4, (count / maximum) * 100)}%` : '0%';
                bar.title = `${bar.dataset.rating} estrelas: ${count} avaliações`;
            });
        });
    }

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
            updateRatingSummary(counts);
            updateCharts(counts);
            renderTopDishes(counts.produtos_mais_avaliados || []);
            renderLatestReviews(counts.ultimas_avaliacoes || []);
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
