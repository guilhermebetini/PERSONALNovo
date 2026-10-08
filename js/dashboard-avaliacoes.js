(() => {
    'use strict';

    const status = document.getElementById('reviews-live-status');
    const statElements = {
        total: document.getElementById('review-total-count'),
        atendimento: document.getElementById('review-service-count'),
        pratos: document.getElementById('review-dishes-count'),
        estabelecimento: document.getElementById('review-place-count')
    };
    const topDishesList = document.getElementById('top-dishes-list');
    const reviewsList = document.getElementById('all-reviews-list');
    const filterButtons = [...document.querySelectorAll('.review-filter')];
    let reviews = [];
    let activeFilter = 'todas';
    let loading = false;

    function addEmptyState(container, message) {
        const empty = document.createElement('p');
        empty.className = 'reviews-empty';
        empty.textContent = message;
        container.replaceChildren(empty);
    }

    function renderTopDishes(dishes) {
        topDishesList.replaceChildren();
        if (!dishes.length) {
            addEmptyState(topDishesList, 'Ainda não há avaliações de pratos. Quando os clientes avaliarem, os pratos mais populares aparecerão aqui.');
            return;
        }

        dishes.forEach((dish, index) => {
            const row = document.createElement('article');
            row.className = 'top-dish-row';
            const position = document.createElement('span');
            position.className = 'top-dish-position';
            position.textContent = String(index + 1).padStart(2, '0');
            const info = document.createElement('div');
            info.className = 'top-dish-info';
            const name = document.createElement('h3');
            name.textContent = dish.dish_name;
            const average = document.createElement('p');
            average.textContent = `Média ${Number(dish.media).toFixed(1).replace('.', ',')} de 5`;
            info.append(name, average);
            const total = document.createElement('strong');
            total.className = 'top-dish-total';
            total.append(document.createTextNode(String(dish.total)));
            const totalLabel = document.createElement('span');
            totalLabel.textContent = dish.total === 1 ? 'avaliação' : 'avaliações';
            total.append(totalLabel);
            row.append(position, info, total);
            topDishesList.append(row);
        });
    }

    function renderReviews() {
        const visibleReviews = activeFilter === 'todas'
            ? reviews
            : reviews.filter((review) => review.categoria === activeFilter);
        reviewsList.replaceChildren();
        if (!visibleReviews.length) {
            addEmptyState(
                reviewsList,
                activeFilter === 'todas'
                    ? 'Ainda não há avaliações registradas.'
                    : 'Não há avaliações nesta categoria.'
            );
            return;
        }

        visibleReviews.forEach((review) => {
            const card = document.createElement('article');
            card.className = 'evaluation-review';
            const header = document.createElement('div');
            header.className = 'evaluation-review-header';
            const category = document.createElement('span');
            category.className = 'evaluation-review-category';
            category.dataset.category = review.categoria;
            category.textContent = review.categoria_label;
            const date = document.createElement('time');
            date.className = 'evaluation-review-date';
            const parsedDate = new Date(review.criada_em);
            date.dateTime = review.criada_em;
            date.textContent = Number.isNaN(parsedDate.getTime())
                ? ''
                : parsedDate.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
            header.append(category, date);

            const title = document.createElement('h3');
            title.className = 'evaluation-review-title';
            title.textContent = review.categoria === 'pratos'
                ? (review.prato || 'Avaliação de prato')
                : `Avaliação de ${review.categoria_label.toLowerCase()}`;

            const stars = document.createElement('div');
            stars.className = 'evaluation-review-stars';
            stars.setAttribute('aria-label', `Nota ${review.nota} de 5`);
            stars.textContent = `${'★'.repeat(review.nota)}${'☆'.repeat(5 - review.nota)}`;

            const comment = document.createElement('p');
            comment.className = 'evaluation-review-comment';
            comment.textContent = review.comentario || 'O cliente não deixou um comentário.';
            card.append(header, title, stars, comment);
            reviewsList.append(card);
        });
    }

    async function refreshReviews() {
        if (loading) return;
        loading = true;
        try {
            const response = await fetch('/api/avaliacoes/', { cache: 'no-store' });
            if (!response.ok) throw new Error('Não foi possível carregar as avaliações.');
            const data = await response.json();
            Object.entries(statElements).forEach(([key, element]) => {
                if (element && Number.isInteger(data[key])) element.textContent = String(data[key]);
            });
            reviews = Array.isArray(data.ultimas_avaliacoes) ? data.ultimas_avaliacoes : [];
            renderTopDishes(Array.isArray(data.produtos_mais_avaliados) ? data.produtos_mais_avaliados : []);
            renderReviews();
            status.textContent = `Atualizado às ${new Date().toLocaleTimeString('pt-BR')}. Atualização automática a cada 5 segundos.`;
            status.classList.remove('is-error');
        } catch (error) {
            status.textContent = error.message;
            status.classList.add('is-error');
            if (!reviews.length) {
                reviewsList.replaceChildren();
                const message = document.createElement('p');
                message.className = 'reviews-error';
                message.textContent = 'Não foi possível carregar as avaliações. Verifique se o servidor está ativo e tente novamente.';
                reviewsList.append(message);
            }
        } finally {
            loading = false;
        }
    }

    filterButtons.forEach((button) => {
        button.addEventListener('click', () => {
            activeFilter = button.dataset.filter;
            filterButtons.forEach((item) => {
                const selected = item === button;
                item.classList.toggle('is-active', selected);
                item.setAttribute('aria-pressed', String(selected));
            });
            renderReviews();
        });
    });

    const burger = document.querySelector('.burger');
    const menu = document.querySelector('.menu');
    const sidebar = document.querySelector('.sidebar');
    if (burger && menu && sidebar) {
        burger.addEventListener('click', () => {
            const open = !sidebar.classList.contains('open');
            sidebar.classList.toggle('open', open);
            menu.classList.toggle('is-open', open);
            burger.classList.toggle('is-open', open);
            burger.setAttribute('aria-expanded', String(open));
            burger.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
        });
    }
    refreshReviews();
    window.setInterval(refreshReviews, 5000);
})();
