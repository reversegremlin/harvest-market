document.addEventListener('DOMContentLoaded', function() {
    // Get form elements with null checks
    const form = document.querySelector('form');
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const requirementsList = document.getElementById('password-requirements-list');

    // Early return if required elements are not found
    if (!form || !newPasswordInput || !confirmPasswordInput || !requirementsList) {
        console.error('Required form elements not found');
        return;
    }

    const requirements = {
        length: { id: 'req-length', test: (password) => password.length >= 8 },
        letter: { id: 'req-letter', test: (password) => /[A-Za-z]/.test(password) },
        number: { id: 'req-number', test: (password) => /\d/.test(password) },
        special: { id: 'req-special', test: (password) => /[@$!%*#?&]/.test(password) }
    };

    function updateRequirementUI(elementId, isValid) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.toggle('text-success', isValid);
            element.classList.toggle('text-muted', !isValid);
        }
    }

    function validatePassword(password) {
        let isValid = true;
        
        // Check each requirement
        for (const [key, requirement] of Object.entries(requirements)) {
            const requirementMet = requirement.test(password);
            updateRequirementUI(requirement.id, requirementMet);
            isValid = isValid && requirementMet;
        }

        return isValid;
    }

    function updatePasswordValidation() {
        if (!newPasswordInput) return;

        const password = newPasswordInput.value;
        const isValid = validatePassword(password);

        // Update input validation classes
        newPasswordInput.classList.toggle('is-valid', isValid && password.length > 0);
        newPasswordInput.classList.toggle('is-invalid', !isValid && password.length > 0);

        // If confirm password has a value, validate it as well
        if (confirmPasswordInput && confirmPasswordInput.value) {
            validatePasswordMatch();
        }
    }

    function validatePasswordMatch() {
        if (!newPasswordInput || !confirmPasswordInput) return;

        const isMatch = newPasswordInput.value === confirmPasswordInput.value;
        const confirmValue = confirmPasswordInput.value;

        confirmPasswordInput.classList.toggle('is-valid', isMatch && confirmValue.length > 0);
        confirmPasswordInput.classList.toggle('is-invalid', !isMatch && confirmValue.length > 0);
    }

    // Event Listeners
    newPasswordInput.addEventListener('input', updatePasswordValidation);
    confirmPasswordInput.addEventListener('input', validatePasswordMatch);

    form.addEventListener('submit', function(e) {
        const password = newPasswordInput.value;
        const isValid = validatePassword(password);
        const isMatch = password === confirmPasswordInput.value;

        if (!form.checkValidity() || !isValid || !isMatch) {
            e.preventDefault();
            e.stopPropagation();
        }
        form.classList.add('was-validated');
    });
});
