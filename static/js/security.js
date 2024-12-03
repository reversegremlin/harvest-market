document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordRequirements = {
        length: false,
        letter: false,
        number: false,
        special: false
    };

    function updatePasswordStrength(password) {
        passwordRequirements.length = password.length >= 8;
        passwordRequirements.letter = /[A-Za-z]/.test(password);
        passwordRequirements.number = /\d/.test(password);
        passwordRequirements.special = /[@$!%*#?&]/.test(password);

        // Update UI feedback
        document.querySelectorAll('.password-requirements li').forEach(li => {
            const text = li.textContent.toLowerCase();
            if (text.includes('8 characters') && passwordRequirements.length) {
                li.classList.add('text-success');
                li.classList.remove('text-muted');
            } else if (text.includes('letter') && passwordRequirements.letter) {
                li.classList.add('text-success');
                li.classList.remove('text-muted');
            } else if (text.includes('number') && passwordRequirements.number) {
                li.classList.add('text-success');
                li.classList.remove('text-muted');
            } else if (text.includes('special') && passwordRequirements.special) {
                li.classList.add('text-success');
                li.classList.remove('text-muted');
            } else {
                li.classList.remove('text-success');
                li.classList.add('text-muted');
            }
        });

        const isValid = Object.values(passwordRequirements).every(Boolean);
        newPasswordInput.classList.toggle('is-valid', isValid);
        newPasswordInput.classList.toggle('is-invalid', !isValid && password.length > 0);
    }

    function validatePasswordMatch() {
        const isMatch = newPasswordInput.value === confirmPasswordInput.value;
        confirmPasswordInput.classList.toggle('is-valid', isMatch && confirmPasswordInput.value.length > 0);
        confirmPasswordInput.classList.toggle('is-invalid', !isMatch && confirmPasswordInput.value.length > 0);
    }

    newPasswordInput.addEventListener('input', function() {
        updatePasswordStrength(this.value);
        validatePasswordMatch();
    });

    confirmPasswordInput.addEventListener('input', validatePasswordMatch);

    form.addEventListener('submit', function(e) {
        if (!form.checkValidity() || 
            !Object.values(passwordRequirements).every(Boolean) || 
            newPasswordInput.value !== confirmPasswordInput.value) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });
});
