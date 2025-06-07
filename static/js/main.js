// main.js - JavaScript for Transaction Categorizer app

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add highlighting effect when adding or removing categories
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('highlight')) {
        const highlightId = urlParams.get('highlight');
        const element = document.getElementById('transaction-' + highlightId);
        if (element) {
            element.classList.add('highlight-animation');
            setTimeout(() => {
                element.classList.remove('highlight-animation');
            }, 2000);
        }
    }
});