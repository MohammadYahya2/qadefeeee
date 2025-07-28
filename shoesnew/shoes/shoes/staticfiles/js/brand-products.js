// Brand Products Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Image Lazy Loading with Fallback
    initImageLazyLoading();
    
    // Initialize Quick Add to Cart
    initQuickAddToCart();
    
    // Initialize Tooltips
    initTooltips();
    
    // Handle Image Loading Errors
    handleImageErrors();
    
    // Initialize Smooth Animations
    initAnimations();
});

// Image Lazy Loading Implementation
function initImageLazyLoading() {
    const images = document.querySelectorAll('img[loading="lazy"]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    loadImage(img);
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        images.forEach(img => loadImage(img));
    }
}

// Load Image with Animation
function loadImage(img) {
    img.addEventListener('load', function() {
        img.classList.add('loaded');
    });
    
    img.addEventListener('error', function() {
        handleImageError(img);
    });
    
    // Trigger loading if src is already set
    if (img.complete) {
        img.classList.add('loaded');
    }
}

// Handle Image Loading Errors
function handleImageErrors() {
    const images = document.querySelectorAll('.product-image');
    
    images.forEach(img => {
        img.addEventListener('error', function() {
            handleImageError(img);
        });
    });
}

// Image Error Handler
function handleImageError(img) {
    const container = img.closest('.product-image-container');
    if (container) {
        // Create placeholder
        const placeholder = document.createElement('div');
        placeholder.className = 'no-image-placeholder';
        placeholder.innerHTML = `
            <i class="fas fa-image"></i>
            <p>لا توجد صورة</p>
        `;
        
        // Replace image with placeholder
        container.innerHTML = '';
        container.appendChild(placeholder);
    }
}

// Quick Add to Cart
function initQuickAddToCart() {
    const quickAddForms = document.querySelectorAll('.quick-add-form');
    
    quickAddForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = this.querySelector('button');
            const originalContent = btn.innerHTML;
            
            // Show loading state
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            btn.disabled = true;
            
            try {
                const formData = new FormData(this);
                const response = await fetch(this.action || '/add-to-cart/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast('تمت الإضافة إلى السلة بنجاح', 'success');
                    updateCartCount(data.cart_count);
                    
                    // Animate button success
                    btn.innerHTML = '<i class="fas fa-check"></i>';
                    btn.classList.add('success');
                    
                    setTimeout(() => {
                        btn.innerHTML = originalContent;
                        btn.classList.remove('success');
                    }, 2000);
                } else {
                    showToast(data.message || 'حدث خطأ في إضافة المنتج', 'error');
                    btn.innerHTML = originalContent;
                }
            } catch (error) {
                console.error('Error:', error);
                showToast('حدث خطأ في الاتصال بالخادم', 'error');
                btn.innerHTML = originalContent;
            } finally {
                btn.disabled = false;
            }
        });
    });
}

// Show Toast Notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-triangle' : 'info-circle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon} toast-icon"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Create Toast Container
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Update Cart Count
function updateCartCount(count) {
    const badges = document.querySelectorAll('.cart-badge, [data-cart-count]');
    badges.forEach(badge => {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
        
        // Animate badge
        badge.classList.add('pulse');
        setTimeout(() => badge.classList.remove('pulse'), 1000);
    });
}

// Initialize Tooltips
function initTooltips() {
    const elements = document.querySelectorAll('[title]');
    
    elements.forEach(element => {
        const title = element.getAttribute('title');
        element.removeAttribute('title');
        element.setAttribute('data-tooltip', title);
        
        element.addEventListener('mouseenter', function(e) {
            showTooltip(e.target, title);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

// Show Tooltip
function showTooltip(element, text) {
    hideTooltip(); // Remove any existing tooltip
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    // Position tooltip
    tooltip.style.left = rect.left + (rect.width - tooltipRect.width) / 2 + 'px';
    tooltip.style.top = rect.top - tooltipRect.height - 10 + 'px';
    
    // Add active class for animation
    setTimeout(() => tooltip.classList.add('active'), 10);
}

// Hide Tooltip
function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Initialize Animations
function initAnimations() {
    // Animate products on scroll
    const products = document.querySelectorAll('.modern-card');
    
    if ('IntersectionObserver' in window) {
        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('animate-in');
                    }, index * 50);
                }
            });
        }, {
            threshold: 0.1
        });
        
        products.forEach(product => {
            product.style.opacity = '0';
            product.style.transform = 'translateY(20px)';
            animationObserver.observe(product);
        });
    }
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        opacity: 1 !important;
        transform: translateY(0) !important;
        transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .pulse {
        animation: pulse 1s ease;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
    
    @keyframes slideOut {
        to {
            transform: translateX(-110%);
            opacity: 0;
        }
    }
    
    .tooltip {
        position: fixed;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        z-index: 9999;
        pointer-events: none;
        opacity: 0;
        transform: translateY(5px);
        transition: all 0.2s ease;
    }
    
    .tooltip.active {
        opacity: 1;
        transform: translateY(0);
    }
    
    .quick-action-btn.success {
        background: #10b981 !important;
    }
`;
document.head.appendChild(style);

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for external use
window.BrandProducts = {
    showToast,
    updateCartCount,
    initImageLazyLoading
}; 