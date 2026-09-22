function handleSearch() {
    const searchInput = document.querySelector('.search input[type="text"]');
    if (!searchInput) {
        return;
    }

    const query = searchInput.value.trim();

    if (query) {
        window.location.href = `search.html?q=${encodeURIComponent(query)}`;
    }
}

const searchButton = document.querySelector('.search button');
if (searchButton) {
    searchButton.addEventListener('click', handleSearch);
}

const searchInput = document.querySelector('.search input[type="text"]');
if (searchInput) {
    searchInput.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            handleSearch();
        }
    });
}
