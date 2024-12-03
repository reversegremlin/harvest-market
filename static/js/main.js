// Form validation
document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Password confirmation validation
    const passwordConfirmation = document.getElementById('confirm_password');
    if (passwordConfirmation) {
        passwordConfirmation.addEventListener('input', function() {
            const password = document.querySelector('#password').value;
            const isMatch = this.value === password;
            this.setCustomValidity(isMatch ? '' : 'Passwords do not match');
        });
    }

    // Password strength indicator
    const passwordInput = document.querySelector('input[type="password"]');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const strength = calculatePasswordStrength(this.value);
            updatePasswordStrengthIndicator(strength);
        });
    }

    // Autumn leaves animation
    createLeaves();
});

function calculatePasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    return Math.min(5, strength);
}

function updatePasswordStrengthIndicator(strength) {
    const indicator = document.getElementById('password-strength');
    if (!indicator) return;
    
    const strengthLabels = ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'];
    const strengthColors = ['danger', 'danger', 'warning', 'info', 'success'];
    
    indicator.textContent = `Strength: ${strengthLabels[strength - 1] || ''}`;
    indicator.className = `text-${strengthColors[strength - 1] || 'danger'}`;
}

// Autumn theme animations
function createLeaves() {
    const leafCount = 20;
    const container = document.body;
    
    for (let i = 0; i < leafCount; i++) {
        setTimeout(() => {
            const leaf = document.createElement('div');
            leaf.className = 'leaf-decoration';
            leaf.style.left = `${Math.random() * 100}vw`;
            leaf.style.animationDelay = `${Math.random() * 10}s`;
            
            // Use the SVG as background
            leaf.style.backgroundImage = `url('${window.location.origin}/static/img/autumn-leaf.svg')`;
            leaf.style.backgroundSize = 'contain';
            leaf.style.backgroundRepeat = 'no-repeat';
            
            container.appendChild(leaf);
            
            // Remove leaf after animation
            leaf.addEventListener('animationend', () => {
                leaf.remove();
            });
        }, i * 500);
    }
    
    // Recreate leaves periodically
    setTimeout(createLeaves, leafCount * 500);
}
