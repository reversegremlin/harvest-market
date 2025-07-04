// Define validateAge function in global scope
function validateAge(input) {
    if (!input.value) {
        input.setCustomValidity('Please enter your date of birth');
        return false;
    }

    const birthDate = new Date(input.value);
    const today = new Date();
    const minAgeDate = new Date();
    minAgeDate.setFullYear(today.getFullYear() - 16);

    if (birthDate > minAgeDate) {
        input.setCustomValidity('You must be at least 16 years old to register');
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        return false;
    } else {
        input.setCustomValidity('');
        input.classList.add('is-valid');
        input.classList.remove('is-invalid');
        return true;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('username');
    const usernameValidation = document.getElementById('username-validation');
    const birthDateInput = document.getElementById('birth_date');
    let debounceTimer;

    function validateUsername() {
        const username = usernameInput.value.trim();
        
        // Clear previous validation
        usernameInput.classList.remove('is-valid', 'is-invalid');
        if (usernameValidation) {
            usernameValidation.textContent = '';
            usernameValidation.classList.remove('text-success', 'text-danger');
        }

        if (username.length < 3) {
            return; // Don't check too short usernames
        }

        // Show loading state
        if (usernameValidation) {
            usernameValidation.textContent = 'Checking username...';
            usernameValidation.classList.add('text-muted');
        }

        // Create form data
        const formData = new FormData();
        formData.append('username', username);

        // Get CSRF token
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (!csrfMeta) {
            console.error('CSRF token meta tag not found');
            if (usernameValidation) {
                usernameValidation.textContent = 'Error: CSRF protection unavailable';
                usernameValidation.classList.remove('text-success', 'text-muted');
                usernameValidation.classList.add('text-danger');
            }
            return;
        }
        
        const csrfToken = csrfMeta.getAttribute('content');
        if (!csrfToken) {
            console.error('CSRF token is empty');
            if (usernameValidation) {
                usernameValidation.textContent = 'Error: CSRF token missing';
                usernameValidation.classList.remove('text-success', 'text-muted');
                usernameValidation.classList.add('text-danger');
            }
            return;
        }

        // Send request
        fetch('/auth/check-username', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (usernameValidation) {
                usernameValidation.textContent = data.message;
                if (data.available) {
                    usernameValidation.classList.remove('text-danger', 'text-muted');
                    usernameValidation.classList.add('text-success');
                    usernameInput.classList.add('is-valid');
                    usernameInput.classList.remove('is-invalid');
                } else {
                    usernameValidation.classList.remove('text-success', 'text-muted');
                    usernameValidation.classList.add('text-danger');
                    usernameInput.classList.add('is-invalid');
                    usernameInput.classList.remove('is-valid');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (usernameValidation) {
                usernameValidation.textContent = 'Error checking username availability';
                usernameValidation.classList.remove('text-success', 'text-muted');
                usernameValidation.classList.add('text-danger');
            }
        });
    }

    if (usernameInput) {
        usernameInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(validateUsername, 500); // Debounce for 500ms
        });
    }

    if (birthDateInput) {
        birthDateInput.addEventListener('change', function() {
            validateAge(this);
        });

        // Set max date to today
        const today = new Date();
        const dd = String(today.getDate()).padStart(2, '0');
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const yyyy = today.getFullYear();
        birthDateInput.max = `${yyyy}-${mm}-${dd}`;
    }
});
