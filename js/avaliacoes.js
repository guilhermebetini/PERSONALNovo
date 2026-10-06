(() => {
    'use strict';

    const DISHES_KEY = 'opiniaki_dishes_v1';
    const REVIEWS_KEY = 'opiniaki_reviews_v1';
    const MAX_IMAGE_SIZE = 1.5 * 1024 * 1024;
    const initialDishes = [
        { id: 'combo-sushi', name: 'Combo Sushi Especial', category: 'Sushi', description: 'Seleção do chef com sushis frescos e peças especiais.', image: '/static/imgs/imagemtelainicial.png' },
        { id: 'temaki-salmao', name: 'Temaki de Salmão', category: 'Sushi', description: 'Salmão fresco, arroz temperado e alga crocante.', image: '/static/imgs/imagem1.avif' },
        { id: 'yakisoba', name: 'Yakisoba', category: 'Prato quente', description: 'Macarrão salteado com legumes frescos e molho da casa.', image: '/static/imgs/imagem2.webp' },
        { id: 'hot-roll', name: 'Hot Roll', category: 'Sushi', description: 'Sushi empanado e crocante, servido com molho especial.', image: '/static/imgs/imagem3.jpg' },
        { id: 'petit-gateau', name: 'Petit Gâteau', category: 'Sobremesa', description: 'Bolo de chocolate com recheio cremoso e sorvete.', image: '/static/imgs/qualidade boa.webp' }
    ];

    const clone = (value) => JSON.parse(JSON.stringify(value));

    function getStoredArray(key, fallback = []) {
        try {
            const value = localStorage.getItem(key);
            if (!value) return clone(fallback);
            const parsed = JSON.parse(value);
            return Array.isArray(parsed) ? parsed : clone(fallback);
        } catch (_) {
            return clone(fallback);
        }
    }

    function storeArray(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (_) {
            return false;
        }
    }

    function getCsrfToken() {
        const token = document.cookie
            .split('; ')
            .find((cookie) => cookie.startsWith('csrftoken='));
        return token ? decodeURIComponent(token.slice('csrftoken='.length)) : '';
    }

    async function submitEvaluation(evaluation) {
        const response = await fetch('/api/avaliacoes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(evaluation)
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Não foi possível enviar sua avaliação.');
        }
        return result;
    }

    function setStatus(element, message, isError = false) {
        if (!element) return;
        element.textContent = message;
        element.classList.toggle('is-error', isError);
    }

    function setupNavigation() {
        const burger = document.querySelector('.burger');
        const menu = document.querySelector('.menu');
        if (!burger || !menu) return;

        const toggleMenu = (open) => {
            menu.classList.toggle('is-open', open);
            burger.classList.toggle('is-open', open);
            burger.setAttribute('aria-expanded', String(open));
            burger.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
        };

        burger.addEventListener('click', () => toggleMenu(!menu.classList.contains('is-open')));
        menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => toggleMenu(false)));
    }

    function setupRatingGroups(scope = document) {
        scope.querySelectorAll('[data-rating-group]').forEach((group) => {
            const buttons = [...group.querySelectorAll('.star-button')];
            const input = group.parentElement.querySelector('input[name="rating"]');
            const feedback = group.parentElement.querySelector('.rating-feedback');

            const update = (value, announce = true) => {
                const score = Number(value);
                buttons.forEach((button) => {
                    const selected = Number(button.dataset.value) <= score;
                    button.classList.toggle('is-selected', selected);
                    button.setAttribute('aria-pressed', String(Number(button.dataset.value) === score));
                });
                if (input) input.value = score ? String(score) : '';
                if (feedback && announce) feedback.textContent = score ? `${score} ${score === 1 ? 'estrela selecionada' : 'estrelas selecionadas'}.` : '';
            };

            buttons.forEach((button, index) => {
                button.addEventListener('click', () => update(button.dataset.value));
                button.addEventListener('keydown', (event) => {
                    let nextIndex = index;
                    if (event.key === 'ArrowRight' || event.key === 'ArrowUp') nextIndex = Math.min(index + 1, buttons.length - 1);
                    else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') nextIndex = Math.max(index - 1, 0);
                    else if (event.key === 'Home') nextIndex = 0;
                    else if (event.key === 'End') nextIndex = buttons.length - 1;
                    else return;
                    event.preventDefault();
                    buttons[nextIndex].focus();
                    update(buttons[nextIndex].dataset.value);
                });
            });
        });
    }

    function clearRating(form) {
        const input = form.querySelector('input[name="rating"]');
        if (input) input.value = '';
        form.querySelectorAll('.star-button').forEach((button) => {
            button.classList.remove('is-selected');
            button.setAttribute('aria-pressed', 'false');
        });
        const feedback = form.querySelector('.rating-feedback');
        if (feedback) feedback.textContent = '';
    }

    function createDishCard(dish) {
        const card = document.createElement('article');
        card.className = 'dish-card';

        if (dish.image) {
            const image = document.createElement('img');
            image.className = 'dish-image';
            image.src = dish.image;
            image.alt = dish.name;
            image.loading = 'lazy';
            image.addEventListener('error', () => {
                image.replaceWith(createDishPlaceholder());
            }, { once: true });
            card.append(image);
        } else {
            card.append(createDishPlaceholder());
        }

        const content = document.createElement('div');
        content.className = 'dish-card-content';
        const category = document.createElement('span');
        category.className = 'dish-category';
        category.textContent = dish.category;
        const title = document.createElement('h3');
        title.textContent = dish.name;
        const description = document.createElement('p');
        description.textContent = dish.description;
        const actions = document.createElement('div');
        actions.className = 'dish-actions';
        const reviewButton = document.createElement('button');
        reviewButton.type = 'button';
        reviewButton.className = 'button-primary';
        reviewButton.dataset.action = 'review';
        reviewButton.dataset.id = dish.id;
        reviewButton.textContent = 'Avaliar este prato';
        actions.append(reviewButton);
        content.append(category, title, description, actions);
        card.append(content);
        return card;
    }

    function createDishPlaceholder() {
        const placeholder = document.createElement('div');
        placeholder.className = 'dish-image dish-image--placeholder';
        placeholder.setAttribute('aria-hidden', 'true');
        placeholder.textContent = '✦';
        return placeholder;
    }

    function setupDishPage() {
        const list = document.getElementById('dish-list');
        if (!list) return;
        const count = document.getElementById('dish-count');
        const reviewArea = document.getElementById('dish-review-area');
        const reviewForm = document.getElementById('dish-review-form');
        const reviewStatus = document.getElementById('dish-review-status');
        const reviewedDishId = document.getElementById('reviewed-dish-id');
        const selectedDishName = document.getElementById('selected-dish-name');
        let dishes = getStoredArray(DISHES_KEY, initialDishes);

        const render = () => {
            list.replaceChildren();
            count.textContent = `${dishes.length} ${dishes.length === 1 ? 'prato disponível' : 'pratos disponíveis'}`;
            if (!dishes.length) {
                const empty = document.createElement('p');
                empty.className = 'empty-state';
                empty.textContent = 'Nenhum prato cadastrado ainda. Cadastre pratos pelo Dashboard.';
                list.append(empty);
                return;
            }
            dishes.forEach((dish) => list.append(createDishCard(dish)));
        };

        window.addEventListener('storage', (event) => {
            if (event.key !== DISHES_KEY) return;
            dishes = getStoredArray(DISHES_KEY, initialDishes);
            render();
        });

        const closeReview = () => {
            reviewArea.hidden = true;
            reviewForm.reset();
            clearRating(reviewForm);
            setStatus(reviewStatus, '');
        };

        list.addEventListener('click', (event) => {
            const button = event.target.closest('button[data-action]');
            if (!button) return;
            const dish = dishes.find((item) => item.id === button.dataset.id);
            if (!dish) return;
            reviewedDishId.value = dish.id;
            selectedDishName.textContent = dish.name;
            reviewForm.reset();
            clearRating(reviewForm);
            setStatus(reviewStatus, '');
            reviewArea.hidden = false;
            reviewArea.scrollIntoView({ behavior: 'smooth', block: 'center' });
            reviewArea.querySelector('.star-button').focus();
        });

        document.getElementById('close-dish-review').addEventListener('click', closeReview);
        document.getElementById('cancel-dish-review').addEventListener('click', closeReview);

        reviewForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const rating = Number(reviewForm.elements.rating.value);
            if (!rating) {
                setStatus(reviewStatus, 'Escolha de 1 a 5 estrelas antes de enviar.', true);
                reviewForm.querySelector('.star-button').focus();
                return;
            }
            const dish = dishes.find((item) => item.id === reviewedDishId.value);
            try {
                await submitEvaluation({
                    category: 'pratos',
                    dishId: reviewedDishId.value,
                    dishName: dish ? dish.name : '',
                    rating,
                    comment: reviewForm.elements.comment.value.trim()
                });
            } catch (error) {
                setStatus(reviewStatus, error.message, true);
                return;
            }
            const reviews = getStoredArray(REVIEWS_KEY);
            reviews.push({ id: `review-${Date.now()}`, category: 'pratos', dishId: reviewedDishId.value, rating, comment: reviewForm.elements.comment.value.trim(), createdAt: new Date().toISOString() });
            storeArray(REVIEWS_KEY, reviews);
            reviewForm.reset();
            clearRating(reviewForm);
            setStatus(reviewStatus, 'Obrigado! Sua avaliação foi enviada com sucesso.');
        });

        render();
    }

    function setupDishAdminPage() {
        const form = document.getElementById('dish-registration-form');
        const list = document.getElementById('dashboard-dish-list');
        if (!form || !list) return;

        const status = document.getElementById('dish-registration-status');
        const count = document.getElementById('dashboard-dish-count');
        const productCount = document.getElementById('dashboard-product-count');
        let dishes = getStoredArray(DISHES_KEY, initialDishes);

        const render = () => {
            list.replaceChildren();
            count.textContent = `${dishes.length} ${dishes.length === 1 ? 'prato' : 'pratos'}`;
            if (productCount) productCount.textContent = String(dishes.length);
            if (!dishes.length) {
                const empty = document.createElement('p');
                empty.className = 'dashboard-dish-empty';
                empty.textContent = 'Nenhum prato cadastrado.';
                list.append(empty);
                return;
            }
            dishes.forEach((dish) => {
                const item = document.createElement('article');
                item.className = 'dashboard-dish-item';
                const image = dish.image ? document.createElement('img') : null;
                if (image) {
                    image.src = dish.image;
                    image.alt = '';
                    image.loading = 'lazy';
                    image.addEventListener('error', () => image.remove(), { once: true });
                    item.append(image);
                }
                const details = document.createElement('div');
                details.className = 'dashboard-dish-details';
                const name = document.createElement('h4');
                name.textContent = dish.name;
                const meta = document.createElement('p');
                meta.textContent = `${dish.category} · ${dish.description}`;
                details.append(name, meta);
                const remove = document.createElement('button');
                remove.type = 'button';
                remove.className = 'dashboard-dish-remove';
                remove.dataset.id = dish.id;
                remove.textContent = 'Excluir';
                remove.setAttribute('aria-label', `Excluir ${dish.name}`);
                item.append(details, remove);
                list.append(item);
            });
        };

        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const name = form.elements.name.value.trim();
            const description = form.elements.description.value.trim();
            const imageUrl = form.elements.imageUrl.value.trim();
            const file = form.elements.imageFile.files[0];
            if (!name || !description) {
                setStatus(status, 'Preencha o nome e a descrição do prato.', true);
                return;
            }
            if (imageUrl) {
                try {
                    const url = new URL(imageUrl);
                    if (!['http:', 'https:'].includes(url.protocol)) throw new Error();
                } catch (_) {
                    setStatus(status, 'Informe uma URL de imagem válida, iniciando com http:// ou https://.', true);
                    return;
                }
            }
            if (file && (!file.type.startsWith('image/') || file.size > MAX_IMAGE_SIZE)) {
                setStatus(status, 'Envie uma imagem de até 1,5 MB.', true);
                return;
            }
            const saveDish = (image = imageUrl) => {
                const dish = { id: `dish-${Date.now()}-${Math.random().toString(16).slice(2)}`, name, description, category: form.elements.category.value, image };
                const nextDishes = [...dishes, dish];
                if (!storeArray(DISHES_KEY, nextDishes)) {
                    setStatus(status, 'Não foi possível salvar o prato. Tente uma imagem menor.', true);
                    return;
                }
                dishes = nextDishes;
                form.reset();
                setStatus(status, `“${dish.name}” foi cadastrado e já está disponível para avaliação.`);
                render();
            };
            if (!file) {
                saveDish();
                return;
            }
            const reader = new FileReader();
            reader.addEventListener('load', () => saveDish(String(reader.result)));
            reader.addEventListener('error', () => setStatus(status, 'Não foi possível ler a imagem selecionada.', true));
            reader.readAsDataURL(file);
        });

        list.addEventListener('click', (event) => {
            const button = event.target.closest('.dashboard-dish-remove');
            if (!button) return;
            const dish = dishes.find((item) => item.id === button.dataset.id);
            if (!dish || !window.confirm(`Deseja excluir o prato “${dish.name}”?`)) return;
            const nextDishes = dishes.filter((item) => item.id !== dish.id);
            if (!storeArray(DISHES_KEY, nextDishes)) {
                setStatus(status, 'Não foi possível salvar a remoção neste navegador.', true);
                return;
            }
            dishes = nextDishes;
            setStatus(status, `“${dish.name}” foi removido do cardápio.`);
            render();
        });

        render();
    }

    function setupExperiencePage() {
        const form = document.getElementById('experience-review-form');
        if (!form) return;
        const status = document.getElementById('experience-review-status');
        const category = document.body.dataset.category;
        const categoryLabel = document.body.dataset.categoryLabel || category;
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const rating = Number(form.elements.rating.value);
            if (!rating) {
                setStatus(status, 'Escolha de 1 a 5 estrelas antes de enviar.', true);
                form.querySelector('.star-button').focus();
                return;
            }
            const comment = form.elements.comment.value.trim();
            try {
                await submitEvaluation({ category, rating, comment });
            } catch (error) {
                setStatus(status, error.message, true);
                return;
            }
            const reviews = getStoredArray(REVIEWS_KEY);
            reviews.push({ id: `review-${Date.now()}`, category, rating, comment, createdAt: new Date().toISOString() });
            storeArray(REVIEWS_KEY, reviews);
            form.reset();
            clearRating(form);
            setStatus(status, `Obrigado! Sua avaliação de ${categoryLabel} foi enviada com sucesso.`);
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        setupNavigation();
        setupRatingGroups();
        setupDishPage();
        setupDishAdminPage();
        setupExperiencePage();
    });
})();
