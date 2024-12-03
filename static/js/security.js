document.addEventListener('DOMContentLoaded', function() {
    // Password requirements configuration
    const requirements = {
        length: { id: 'req-length', test: (password) => password.length >= 8, text: 'At least 8 characters' },
        letter: { id: 'req-letter', test: (password) => /[A-Za-z]/.test(password), text: 'At least one letter' },
        number: { id: 'req-number', test: (password) => /\d/.test(password), text: 'At least one number' },
        special: { id: 'req-special', test: (password) => /[@$!%*#?&]/.test(password), text: 'At least one special character (@$!%*#?&)' }
    };

    // Get form elements
    const form = document.querySelector('form.needs-validation');
    const currentPasswordInput = document.getElementById('current_password');
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const requirementsList = document.getElementById('password-requirements-list');

    // Initialize requirement list items if they don't exist
    function initializeRequirementsList() {
        if (!requirementsList) return;
        
        requirementsList.innerHTML = '';
        Object.entries(requirements).forEach(([key, req]) => {
            const li = document.createElement('li');
            li.id = req.id;
            li.className = 'text-muted';
            li.textContent = req.text;
            requirementsList.appendChild(li);
        });
    }

    // Update single requirement UI
    function updateRequirementUI(elementId, isValid) {
        const element = document.getElementById(elementId);
        if (!element) return;

        element.className = isValid ? 'text-success' : 'text-muted';
        element.innerHTML = `${isValid ? '✓' : '×'} ${requirements[elementId.replace('req-', '')].text}`;
    }

    // Validate password against all requirements
    function validatePassword(password = '') {
        let isValid = true;
        
        Object.entries(requirements).forEach(([key, requirement]) => {
            const requirementMet = requirement.test(password);
            updateRequirementUI(requirement.id, requirementMet);
            isValid = isValid && requirementMet;
        });

        return isValid;
    }

    // Real-time password validation
    function updatePasswordValidation() {
        if (!newPasswordInput) return;

        const password = newPasswordInput.value || '';
        const isValid = validatePassword(password);

        newPasswordInput.classList.toggle('is-valid', isValid && password.length > 0);
        newPasswordInput.classList.toggle('is-invalid', !isValid && password.length > 0);

        // Trigger password match validation
        validatePasswordMatch();
    }

    // Real-time password match validation
    function validatePasswordMatch() {
        if (!newPasswordInput || !confirmPasswordInput) return;

        const password = newPasswordInput.value || '';
        const confirmValue = confirmPasswordInput.value || '';
        const isMatch = password === confirmValue;

        if (confirmValue.length > 0) {
            confirmPasswordInput.classList.toggle('is-valid', isMatch);
            confirmPasswordInput.classList.toggle('is-invalid', !isMatch);
        } else {
            confirmPasswordInput.classList.remove('is-valid', 'is-invalid');
        }
    }

    // Initialize requirements list
    initializeRequirementsList();

    // Add event listeners for real-time validation
    if (newPasswordInput) {
        ['input', 'change', 'keyup'].forEach(event => {
            newPasswordInput.addEventListener(event, updatePasswordValidation);
        });
    }

    if (confirmPasswordInput) {
        ['input', 'change', 'keyup'].forEach(event => {
            confirmPasswordInput.addEventListener(event, validatePasswordMatch);
        });
    }

    // Form submission handler
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!newPasswordInput || !confirmPasswordInput || !currentPasswordInput) {
                console.error('Required form elements not found');
                return;
            }

            const password = newPasswordInput.value || '';
            const isValid = validatePassword(password);
            const isMatch = password === (confirmPasswordInput.value || '');

            if (!form.checkValidity() || !isValid || !isMatch) {
                e.stopPropagation();
            } else {
                form.submit();
            }

            form.classList.add('was-validated');
        });
    }
});
