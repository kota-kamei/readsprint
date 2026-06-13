// Form handling and validation
document.addEventListener('DOMContentLoaded', function() {
    const wordContainer = document.getElementById('target-words-container');
    const addWordBtn = document.getElementById('add-word-btn');
    
    if (wordContainer && addWordBtn) {
        // Add new word input
        addWordBtn.addEventListener('click', function() {
            const wordInputs = wordContainer.querySelectorAll('.word-input-group');
            if (wordInputs.length >= 3) {
                return;
            }
            
            const newGroup = document.createElement('div');
            newGroup.className = 'word-input-group';
            
            const input = document.createElement('input');
            input.type = 'text';
            input.name = 'target_words[]';
            input.className = 'word-input';
            input.maxLength = 30;
            input.pattern = '[A-Za-z\\s]+';
            input.placeholder = '単語を入力';
            
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'remove-word-btn';
            removeBtn.innerHTML = '×';
            removeBtn.addEventListener('click', function() {
                newGroup.remove();
                updateAddButtonState();
            });
            
            newGroup.appendChild(input);
            newGroup.appendChild(removeBtn);
            wordContainer.appendChild(newGroup);
            
            updateAddButtonState();
        });
        
        // Update add button state
        function updateAddButtonState() {
            const wordInputs = wordContainer.querySelectorAll('.word-input-group');
            addWordBtn.disabled = wordInputs.length >= 3;
        }
        
        // Input validation
        wordContainer.addEventListener('input', function(e) {
            if (e.target.classList.contains('word-input')) {
                const input = e.target;
                const value = input.value;
                
                // Remove any non-alphabet characters and spaces
                const sanitizedValue = value.replace(/[^A-Za-z\s]/g, '');
                if (value !== sanitizedValue) {
                    input.value = sanitizedValue;
                }
            }
        });
    }

    // Show a loading overlay while the text is being generated
    document.querySelectorAll('form.js-loading-form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
            }

            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-spinner"></div>
                <p class="loading-message">文章を生成しています...</p>
            `;
            document.body.appendChild(overlay);
        });
    });
});

// Alert dismissal
document.querySelectorAll('.alert').forEach(alert => {
    const closeButton = document.createElement('button');
    closeButton.innerHTML = '×';
    closeButton.className = 'alert-close';
    closeButton.addEventListener('click', () => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    });
    alert.appendChild(closeButton);
});

// Smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Mobile navigation handling
const createMobileNav = () => {
    const nav = document.querySelector('nav');
    if (!nav) return;

    const menuButton = document.createElement('button');
    menuButton.className = 'mobile-menu-button';
    menuButton.setAttribute('aria-label', 'メニューを開く');
    
    const navLinks = document.querySelector('.nav-links');
    if (!navLinks) return;

    menuButton.addEventListener('click', () => {
        const isExpanded = menuButton.getAttribute('aria-expanded') === 'true';
        menuButton.setAttribute('aria-expanded', !isExpanded);
        navLinks.classList.toggle('active');
    });

    nav.insertBefore(menuButton, navLinks);
};

// Initialize mobile navigation on small screens
if (window.innerWidth <= 768) {
    createMobileNav();
}

// Handle window resize
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const mobileButton = document.querySelector('.mobile-menu-button');
        if (window.innerWidth <= 768 && !mobileButton) {
            createMobileNav();
        } else if (window.innerWidth > 768 && mobileButton) {
            mobileButton.remove();
            document.querySelector('.nav-links')?.classList.remove('active');
        }
    }, 250);
});