/**
 * Interactive Captcha System
 * Provides checkbox-based verification with image challenges
 */

class InteractiveCaptcha {
    constructor(containerId, challengeType = 'images') {
        this.containerId = containerId;
        this.challengeType = challengeType;
        this.isVerified = false;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.warn(`Captcha container with ID "${containerId}" not found`);
            return;
        }
        
        this.init();
    }
    
    init() {
        this.createCaptchaHTML();
        this.setupEventListeners();
        this.generateChallenge();
    }
    
    createCaptchaHTML() {
        this.container.innerHTML = `
            <div class="captcha-container">
                <div class="captcha-checkbox-container">
                    <input type="checkbox" id="${this.containerId}-checkbox" class="captcha-checkbox">
                    <label for="${this.containerId}-checkbox" class="captcha-label">لست روبوت</label>
                </div>
                <div id="${this.containerId}-challenge" class="captcha-challenge" style="display: none;">
                    <div class="captcha-challenge-header">
                        <h3 id="${this.containerId}-challenge-title">اختر جميع الصور التي تحتوي على أحذية</h3>
                        <button type="button" id="${this.containerId}-refresh" class="captcha-refresh" title="تحديث">↻</button>
                        <button type="button" id="${this.containerId}-close" class="captcha-close" title="إغلاق">×</button>
                    </div>
                    <div id="${this.containerId}-grid" class="captcha-grid"></div>
                    <div class="captcha-actions">
                        <button type="button" id="${this.containerId}-verify" class="captcha-verify-btn">تحقق</button>
                        <button type="button" id="${this.containerId}-skip" class="captcha-skip-btn">تخطي</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        const checkbox = document.getElementById(`${this.containerId}-checkbox`);
        const challengeDiv = document.getElementById(`${this.containerId}-challenge`);
        const refreshBtn = document.getElementById(`${this.containerId}-refresh`);
        const closeBtn = document.getElementById(`${this.containerId}-close`);
        const verifyBtn = document.getElementById(`${this.containerId}-verify`);
        const skipBtn = document.getElementById(`${this.containerId}-skip`);
        
        if (checkbox) {
            checkbox.addEventListener('change', () => {
                if (checkbox.checked && !this.isVerified) {
                    if (challengeDiv) challengeDiv.style.display = 'block';
                    this.generateChallenge();
                } else if (!checkbox.checked) {
                    if (challengeDiv) challengeDiv.style.display = 'none';
                    this.isVerified = false;
                }
            });
        }
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.generateChallenge());
        }
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeChallenge());
        }
        
        if (verifyBtn) {
            verifyBtn.addEventListener('click', () => this.verifySelection());
        }
        
        if (skipBtn) {
            skipBtn.addEventListener('click', () => this.skipChallenge());
        }
    }
    
    generateChallenge() {
        const grid = document.getElementById(`${this.containerId}-grid`);
        if (!grid) return;
        
        grid.innerHTML = '';
        
        // Sample shoe images for the challenge
        const shoeImages = [
            '/static/images/hero.png',
            '/static/images/herobav.png',
            '/static/images/heroo.png',
            '/media/products/Red_White_Simple_Modern_Shoes_New_Collection_Soon_Instagram_Post_1.png',
            '/media/products/Red_White_Simple_Modern_Shoes_New_Collection_Soon_Instagram_Post_3.png',
            '/media/products/Blue_and_Yellow_Modern_Sport_Shoes_Instagram_Post_1.png'
        ];
        
        const nonShoeImages = [
            '/media/brands/asics.png',
            '/media/brands/nik.png',
            '/media/brands/Under-Armour-logo1.png'
        ];
        
        // Mix shoe and non-shoe images
        const allImages = [...shoeImages.slice(0, 4), ...nonShoeImages.slice(0, 2)];
        const shuffled = this.shuffleArray(allImages);
        
        shuffled.forEach((imageSrc, index) => {
            const imageDiv = document.createElement('div');
            imageDiv.className = 'captcha-image';
            imageDiv.dataset.index = index;
            imageDiv.dataset.isShoe = shoeImages.includes(imageSrc) ? 'true' : 'false';
            
            const img = document.createElement('img');
            img.src = imageSrc;
            img.alt = 'Captcha Image';
            img.onerror = () => {
                img.src = '/static/images/hero.png'; // Fallback image
            };
            
            imageDiv.appendChild(img);
            imageDiv.addEventListener('click', () => this.toggleImageSelection(imageDiv));
            grid.appendChild(imageDiv);
        });
    }
    
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
    
    toggleImageSelection(imageDiv) {
        if (imageDiv.classList.contains('selected')) {
            imageDiv.classList.remove('selected');
        } else {
            imageDiv.classList.add('selected');
        }
    }
    
    verifySelection() {
        const grid = document.getElementById(`${this.containerId}-grid`);
        if (!grid) return;
        
        const selectedImages = grid.querySelectorAll('.captcha-image.selected');
        const correctSelections = Array.from(selectedImages).filter(img => 
            img.dataset.isShoe === 'true'
        );
        
        const allShoeImages = grid.querySelectorAll('.captcha-image[data-is-shoe="true"]');
        
        if (correctSelections.length === allShoeImages.length && 
            selectedImages.length === allShoeImages.length) {
            this.isVerified = true;
            this.showSuccess();
        } else {
            this.showError();
        }
    }
    
    showSuccess() {
        const challengeDiv = document.getElementById(`${this.containerId}-challenge`);
        const checkbox = document.getElementById(`${this.containerId}-checkbox`);
        
        if (challengeDiv) challengeDiv.style.display = 'none';
        if (checkbox) {
            checkbox.checked = true;
            checkbox.disabled = true;
        }
        
        // Show success message
        const successMsg = document.createElement('div');
        successMsg.className = 'captcha-success';
        successMsg.textContent = 'تم التحقق بنجاح!';
        successMsg.style.color = 'green';
        successMsg.style.fontSize = '12px';
        successMsg.style.marginTop = '5px';
        
        const container = document.querySelector(`#${this.containerId} .captcha-checkbox-container`);
        if (container) {
            const existingMsg = container.querySelector('.captcha-success, .captcha-error');
            if (existingMsg) existingMsg.remove();
            container.appendChild(successMsg);
        }
    }
    
    showError() {
        const errorMsg = document.createElement('div');
        errorMsg.className = 'captcha-error';
        errorMsg.textContent = 'اختيار خاطئ، حاول مرة أخرى';
        errorMsg.style.color = 'red';
        errorMsg.style.fontSize = '12px';
        errorMsg.style.marginTop = '5px';
        
        const container = document.querySelector(`#${this.containerId} .captcha-checkbox-container`);
        if (container) {
            const existingMsg = container.querySelector('.captcha-success, .captcha-error');
            if (existingMsg) existingMsg.remove();
            container.appendChild(errorMsg);
            
            // Remove error message after 3 seconds
            setTimeout(() => {
                if (errorMsg.parentNode) {
                    errorMsg.parentNode.removeChild(errorMsg);
                }
            }, 3000);
        }
        
        // Regenerate challenge
        setTimeout(() => this.generateChallenge(), 1000);
    }
    
    closeChallenge() {
        const challengeDiv = document.getElementById(`${this.containerId}-challenge`);
        const checkbox = document.getElementById(`${this.containerId}-checkbox`);
        
        if (challengeDiv) challengeDiv.style.display = 'none';
        if (checkbox) checkbox.checked = false;
        this.isVerified = false;
    }
    
    skipChallenge() {
        this.generateChallenge();
    }
    
    reset() {
        this.isVerified = false;
        const checkbox = document.getElementById(`${this.containerId}-checkbox`);
        const challengeDiv = document.getElementById(`${this.containerId}-challenge`);
        
        if (checkbox) {
            checkbox.checked = false;
            checkbox.disabled = false;
        }
        if (challengeDiv) challengeDiv.style.display = 'none';
        
        // Remove any success/error messages
        const container = document.querySelector(`#${this.containerId} .captcha-checkbox-container`);
        if (container) {
            const messages = container.querySelectorAll('.captcha-success, .captcha-error');
            messages.forEach(msg => msg.remove());
        }
    }
}

// Global captcha instances
window.captchaInstances = {};

// Initialize captcha function
function initializeCaptcha(containerId, challengeType = 'images') {
    const container = document.getElementById(containerId);
    if (container) {
        window.captchaInstances[containerId] = new InteractiveCaptcha(containerId, challengeType);
        return window.captchaInstances[containerId];
    }
    return null;
}

// Helper function to validate captcha
function validateCaptcha(containerId) {
    const instance = window.captchaInstances[containerId];
    return instance ? instance.isVerified : false;
}

// Initialize captchas when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize captchas for different forms
    const captchaContainers = [
        'captcha-container-checkout',
        'captcha-container-contact', 
        'captcha-container-register',
        'captcha-container-login'
    ];
    
    captchaContainers.forEach(containerId => {
        const container = document.getElementById(containerId);
        if (container) {
            initializeCaptcha(containerId);
        }
    });
}); 