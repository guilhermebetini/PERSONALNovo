// Function to handle search
function handleSearch() {
    const searchInput = document.querySelector('.search input[type="text"]');
    const query = searchInput.value.trim();

    if (query) {
        // Redirect to the search results page or a specific page
        window.location.href = `search.html?q=${encodeURIComponent(query)}`;
    }
}

// Event listener for the search button
document.querySelector('.search button').addEventListener('click', handleSearch);

// Optional: Allow pressing 'Enter' to trigger the search
document.querySelector('.search input[type="text"]').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        handleSearch();
    }
});
