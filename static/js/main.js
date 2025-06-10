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

    // AJAX Category Management
    initializeCategoryAjax();
});

function initializeCategoryAjax() {
    console.log('Initializing AJAX category management...');
    
    // Handle category form submissions with AJAX
    const forms = document.querySelectorAll('[id^="categorize-form-"]');
    console.log(`Found ${forms.length} category forms`);
    forms.forEach(form => {
        form.addEventListener('submit', handleCategorySubmission);
    });

    // Handle category removal with AJAX  
    const removeLinks = document.querySelectorAll('.remove-category-link');
    console.log(`Found ${removeLinks.length} remove category links`);
    removeLinks.forEach(link => {
        link.addEventListener('click', handleCategoryRemoval);
    });
    
    console.log('AJAX category management initialized successfully');
}

async function handleCategorySubmission(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const transactionId = form.id.split('-')[2]; // Extract ID from "categorize-form-123"
    const submitButton = form.querySelector('button[type="submit"]');
    const modal = bootstrap.Modal.getInstance(document.querySelector(`#addCategoryModal-${transactionId}`));
    
    // Show loading state
    setButtonLoading(submitButton, true);

    try {
        const response = await fetch(`/api/transactions/${transactionId}/categorize`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Add the new category badge to the UI
            addCategoryBadgeToTransaction(transactionId, result.category);
            
            // Reset form and close modal
            form.reset();
            modal.hide();
            
            // Show success notification
            showNotification('Category added successfully!', 'success');
        } else {
            showNotification(result.message || 'Error adding category', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error adding category', 'error');
    } finally {
        setButtonLoading(submitButton, false);
    }
}

async function handleCategoryRemoval(e) {
    e.preventDefault();
    
    const link = e.target;
    let transactionId = link.dataset.transactionId || link.getAttribute('data-transaction-id');
    let categoryId = link.dataset.categoryId || link.getAttribute('data-category-id');
    
    // If we don't have the data attributes, try to extract from the form ID
    if (!transactionId || !categoryId) {
        const form = link.nextElementSibling;
        if (form && form.id) {
            const [, , extractedTransactionId, extractedCategoryId] = form.id.split('-');
            transactionId = transactionId || extractedTransactionId;
            categoryId = categoryId || extractedCategoryId;
        }
    }
    
    if (!transactionId || !categoryId) {
        showNotification('Error: Could not identify transaction or category', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/transactions/${transactionId}/remove-category/${categoryId}`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Remove the category badge from the UI
            removeCategoryBadgeFromTransaction(transactionId, categoryId);
            
            // Show success notification
            showNotification('Category removed successfully!', 'success');
        } else {
            showNotification(result.message || 'Error removing category', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error removing category', 'error');
    }
}

function addCategoryBadgeToTransaction(transactionId, category) {
    // Find the row containing the form for this transaction
    const form = document.querySelector(`#categorize-form-${transactionId}`);
    if (!form) return;
    
    const row = form.closest('tr');
    if (!row) return;
    
    const categoriesCell = row.querySelector('td:nth-child(6)');
    if (!categoriesCell) return;
    
    // Create new badge element
    const badge = document.createElement('span');
    badge.className = 'badge rounded-pill bg-info text-dark mb-1 badge-new';
    badge.innerHTML = `
        ${category.name}
        <a href="#" data-transaction-id="${transactionId}" data-category-id="${category.id}" class="text-danger ms-1 remove-category-link">×</a>
        <form id="remove-category-${transactionId}-${category.id}" action="/transactions/${transactionId}/remove-category/${category.id}" method="post" class="d-none"></form>
    `;
    
    // Add the badge to the categories cell
    categoriesCell.appendChild(badge);
    
    // Set up AJAX for the new remove link
    const newLink = badge.querySelector('.remove-category-link');
    if (newLink) {
        newLink.addEventListener('click', handleCategoryRemoval);
    }
    
    // Remove animation class after animation completes
    setTimeout(() => {
        badge.classList.remove('badge-new');
    }, 2000);
}

function removeCategoryBadgeFromTransaction(transactionId, categoryId) {
    const badge = document.querySelector(`#remove-category-${transactionId}-${categoryId}`).closest('.badge');
    if (badge) {
        badge.style.transition = 'all 0.3s ease';
        badge.style.opacity = '0';
        badge.style.transform = 'scale(0.8)';
        
        setTimeout(() => {
            badge.remove();
        }, 300);
    }
}

function setButtonLoading(button, loading) {
    if (loading) {
        button.classList.add('btn-loading');
        button.disabled = true;
        button.textContent = '';
    } else {
        button.classList.remove('btn-loading');
        button.disabled = false;
        button.textContent = 'Add Category';
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    document.querySelectorAll('.ajax-notification').forEach(n => n.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible ajax-notification`;
    notification.innerHTML = `
        <strong>${type === 'error' ? 'Error!' : type === 'success' ? 'Success!' : 'Info!'}</strong> ${message}
        <button type="button" class="btn-close" aria-label="Close"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Set up close functionality
    const closeBtn = notification.querySelector('.btn-close');
    closeBtn.addEventListener('click', () => {
        hideNotification(notification);
    });
    
    // Auto-hide after 4 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            hideNotification(notification);
        }
    }, 4000);
}

function hideNotification(notification) {
    notification.classList.add('hide');
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.remove();
        }
    }, 300);
}