// Configuration
const API_BASE_URL = 'http://localhost:8000'; // Adjust this to your FastAPI server URL

// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const toggleButton = document.getElementById('toggleButton');
const toggleText = document.getElementById('toggleText');
const brandTitle = document.getElementById('brandTitle');
const brandSubtitle = document.getElementById('brandSubtitle');

// Password toggles
const loginPasswordToggle = document.getElementById('loginPasswordToggle');
const registerPasswordToggle = document.getElementById('registerPasswordToggle');
const confirmPasswordToggle = document.getElementById('confirmPasswordToggle');

// Form inputs
const loginEmail = document.getElementById('loginEmail');
const loginPassword = document.getElementById('loginPassword');
const registerName = document.getElementById('registerName');
const registerEmail = document.getElementById('registerEmail');
const registerPassword = document.getElementById('registerPassword');
const confirmPassword = document.getElementById('confirmPassword');
const roleSelect = document.getElementById('roleSelect');

// Error elements
const loginEmailError = document.getElementById('loginEmailError');
const loginPasswordError = document.getElementById('loginPasswordError');
const registerNameError = document.getElementById('registerNameError');
const registerEmailError = document.getElementById('registerEmailError');
const registerPasswordError = document.getElementById('registerPasswordError');
const confirmPasswordError = document.getElementById('confirmPasswordError');

// Password strength elements
const passwordStrength = document.getElementById('passwordStrength');
const strengthText = document.getElementById('strengthText');

// Buttons
const loginButton = document.getElementById('loginButton');
const registerButton = document.getElementById('registerButton');

// State
let isLoginMode = true;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    updatePasswordStrength();
});

// Event Listeners
function setupEventListeners() {
    // Toggle between login and register
    toggleButton.addEventListener('click', toggleAuthMode);
    
    // Password visibility toggles
    loginPasswordToggle.addEventListener('click', () => togglePasswordVisibility('loginPassword', loginPasswordToggle));
    registerPasswordToggle.addEventListener('click', () => togglePasswordVisibility('registerPassword', registerPasswordToggle));
    confirmPasswordToggle.addEventListener('click', () => togglePasswordVisibility('confirmPassword', confirmPasswordToggle));
    
    // Form submissions
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    
    // Real-time validation
    loginEmail.addEventListener('input', () => validateField('loginEmail'));
    loginPassword.addEventListener('input', () => validateField('loginPassword'));
    registerName.addEventListener('input', () => validateField('registerName'));
    registerEmail.addEventListener('input', () => validateField('registerEmail'));
    registerPassword.addEventListener('input', () => {
        validateField('registerPassword');
        updatePasswordStrength();
        validateField('confirmPassword');
    });
    confirmPassword.addEventListener('input', () => validateField('confirmPassword'));
    
    // Clear errors on focus
    [loginEmail, loginPassword, registerName, registerEmail, registerPassword, confirmPassword].forEach(input => {
        input.addEventListener('focus', () => clearError(input.id));
    });
}

// API Helper Functions
async function makeAPIRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'An error occurred');
        }

        return data;
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// Token management
function saveToken(token) {
    // Store token in memory only (no localStorage)
    window.authToken = token;
}

function getToken() {
    return window.authToken || null;
}

function clearToken() {
    window.authToken = null;
}

// Toggle between login and register modes
function toggleAuthMode() {
    isLoginMode = !isLoginMode;
    
    if (isLoginMode) {
        // Switch to login
        registerForm.classList.remove('active');
        registerForm.classList.add('slide-out');
        
        setTimeout(() => {
            registerForm.classList.remove('slide-out');
            loginForm.classList.add('active');
        }, 250);
        
        brandTitle.textContent = 'Welcome Back';
        brandSubtitle.textContent = 'Sign in to your account to continue';
        toggleText.textContent = "Don't have an account?";
        toggleButton.textContent = 'Sign up';
    } else {
        // Switch to register
        loginForm.classList.remove('active');
        loginForm.classList.add('slide-out');
        
        setTimeout(() => {
            loginForm.classList.remove('slide-out');
            registerForm.classList.add('active');
        }, 250);
        
        brandTitle.textContent = 'Create Account';
        brandSubtitle.textContent = 'Join our library management system';
        toggleText.textContent = 'Already have an account?';
        toggleButton.textContent = 'Sign in';
    }
    
    // Clear all errors and reset forms
    clearAllErrors();
    resetForms();
}

// Password visibility toggle
function togglePasswordVisibility(inputId, toggleButton) {
    const input = document.getElementById(inputId);
    const eyeIcon = toggleButton.querySelector('.eye-icon');
    
    if (input.type === 'password') {
        input.type = 'text';
        eyeIcon.innerHTML = `
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
            <line x1="1" y1="1" x2="23" y2="23"/>
        `;
    } else {
        input.type = 'password';
        eyeIcon.innerHTML = `
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
        `;
    }
}

// Form validation
function validateField(fieldId) {
    const field = document.getElementById(fieldId);
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    switch (fieldId) {
        case 'loginEmail':
        case 'registerEmail':
            if (!value) {
                errorMessage = 'Email is required';
                isValid = false;
            } else if (!isValidEmail(value)) {
                errorMessage = 'Please enter a valid email address';
                isValid = false;
            }
            break;
            
        case 'loginPassword':
            if (!value) {
                errorMessage = 'Password is required';
                isValid = false;
            }
            break;
            
        case 'registerName':
            if (!value) {
                errorMessage = 'Full name is required';
                isValid = false;
            } else if (value.length < 2) {
                errorMessage = 'Name must be at least 2 characters';
                isValid = false;
            }
            break;
            
        case 'registerPassword':
            if (!value) {
                errorMessage = 'Password is required';
                isValid = false;
            } else if (value.length < 8) {
                errorMessage = 'Password must be at least 8 characters';
                isValid = false;
            } else if (!isStrongPassword(value)) {
                errorMessage = 'Password must contain uppercase, lowercase, and numbers';
                isValid = false;
            }
            break;
            
        case 'confirmPassword':
            if (!value) {
                errorMessage = 'Please confirm your password';
                isValid = false;
            } else if (value !== registerPassword.value) {
                errorMessage = 'Passwords do not match';
                isValid = false;
            }
            break;
    }
    
    showError(fieldId, errorMessage, !isValid);
    updateFieldState(field, isValid);
    
    return isValid;
}

// Email validation
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Strong password validation
function isStrongPassword(password) {
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    return hasUpperCase && hasLowerCase && hasNumbers;
}

// Password strength calculation
function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    return strength;
}

// Update password strength indicator
function updatePasswordStrength() {
    const password = registerPassword.value;
    const strength = calculatePasswordStrength(password);
    const bars = document.querySelectorAll('.strength-bar');
    
    if (password.length === 0) {
        passwordStrength.classList.remove('show');
        return;
    }
    
    passwordStrength.classList.add('show');
    
    // Reset all bars
    bars.forEach(bar => {
        bar.classList.remove('weak', 'medium', 'strong');
    });
    
    // Update bars based on strength
    for (let i = 0; i < strength; i++) {
        if (strength <= 2) {
            bars[i].classList.add('weak');
        } else if (strength <= 3) {
            bars[i].classList.add('medium');
        } else {
            bars[i].classList.add('strong');
        }
    }
    
    // Update strength text
    if (strength <= 2) {
        strengthText.textContent = 'Weak password';
        strengthText.style.color = '#ef4444';
    } else if (strength <= 3) {
        strengthText.textContent = 'Medium password';
        strengthText.style.color = '#f59e0b';
    } else {
        strengthText.textContent = 'Strong password';
        strengthText.style.color = '#10b981';
    }
}

// Show/hide error messages
function showError(fieldId, message, show) {
    const errorElement = document.getElementById(fieldId + 'Error');
    
    if (show && message) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    } else {
        errorElement.classList.remove('show');
        setTimeout(() => {
            if (!errorElement.classList.contains('show')) {
                errorElement.textContent = '';
            }
        }, 300);
    }
}

// Clear specific error
function clearError(fieldId) {
    showError(fieldId, '', false);
    const field = document.getElementById(fieldId);
    field.classList.remove('error');
}

// Clear all errors
function clearAllErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    const inputElements = document.querySelectorAll('.auth-input');
    
    errorElements.forEach(error => {
        error.classList.remove('show');
        error.textContent = '';
    });
    
    inputElements.forEach(input => {
        input.classList.remove('error');
    });
}

// Update field visual state
function updateFieldState(field, isValid) {
    if (isValid) {
        field.classList.remove('error');
    } else {
        field.classList.add('error');
    }
}

// Reset forms
function resetForms() {
    loginForm.reset();
    registerForm.reset();
    passwordStrength.classList.remove('show');
}

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    
    // Validate all fields
    const emailValid = validateField('loginEmail');
    const passwordValid = validateField('loginPassword');
    
    if (!emailValid || !passwordValid) {
        return;
    }
    
    // Show loading state
    setButtonLoading(loginButton, true);
    
    try {
        // Prepare form data for OAuth2PasswordRequestForm
        const formData = new FormData();
        formData.append('username', loginEmail.value);
        formData.append('password', loginPassword.value);
        
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }
        
        // Save token and handle successful login
        saveToken(data.access_token);
        
        console.log('Login successful:', {
            email: loginEmail.value,
            token: data.access_token
        });
        
        // Handle successful login
        showSuccessMessage('Login successful! Welcome back!');
        
        // Optional: Redirect to dashboard or main page
        // setTimeout(() => {
        //     window.location.href = '/dashboard.html';
        // }, 1500);
        
    } catch (error) {
        console.error('Login error:', error);
        showError('loginPassword', error.message || 'Invalid email or password', true);
    } finally {
        setButtonLoading(loginButton, false);
    }
}

// Handle register form submission
async function handleRegister(e) {
    e.preventDefault();
    
    // Validate all fields
    const nameValid = validateField('registerName');
    const emailValid = validateField('registerEmail');
    const passwordValid = validateField('registerPassword');
    const confirmPasswordValid = validateField('confirmPassword');
    
    if (!nameValid || !emailValid || !passwordValid || !confirmPasswordValid) {
        return;
    }
    
    // Check terms agreement
    const agreeTerms = document.getElementById('agreeTerms');
    if (!agreeTerms.checked) {
        alert('Please agree to the Terms of Service and Privacy Policy');
        return;
    }
    
    // Show loading state
    setButtonLoading(registerButton, true);
    
    try {
        const userData = {
            name: registerName.value,
            email: registerEmail.value,
            password: registerPassword.value,
            role: roleSelect ? roleSelect.value : 'member'
        };
        
        const response = await makeAPIRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        console.log('Registration successful:', response);
        
        // Handle successful registration
        showSuccessMessage('Account created successfully! You can now sign in.');
        
        // Auto-switch to login form after successful registration
        setTimeout(() => {
            toggleAuthMode();
            loginEmail.value = registerEmail.value; // Pre-fill email
        }, 1500);
        
    } catch (error) {
        console.error('Registration error:', error);
        if (error.message.includes('Email already registered')) {
            showError('registerEmail', 'This email is already registered', true);
        } else {
            showError('registerEmail', error.message || 'Registration failed', true);
        }
    } finally {
        setButtonLoading(registerButton, false);
    }
}

// Set button loading state
function setButtonLoading(button, isLoading) {
    const buttonText = button.querySelector('.button-text');
    const loadingSpinner = button.querySelector('.loading-spinner');
    
    if (isLoading) {
        buttonText.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
        button.disabled = true;
    } else {
        buttonText.classList.remove('hidden');
        loadingSpinner.classList.add('hidden');
        button.disabled = false;
    }
}

// Show success message
function showSuccessMessage(message) {
    // Create and show a temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
        font-weight: 500;
        z-index: 1000;
        animation: slideInRight 0.3s ease;
    `;
    successDiv.textContent = message;
    
    document.body.appendChild(successDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        successDiv.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (document.body.contains(successDiv)) {
                document.body.removeChild(successDiv);
            }
        }, 300);
    }, 3000);
}

// Add success message animations to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        0% {
            opacity: 0;
            transform: translateX(100%);
        }
        100% {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        0% {
            opacity: 1;
            transform: translateX(0);
        }
        100% {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// Add keyboard navigation and other enhancements
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && e.target.classList.contains('toggle-button')) {
        toggleAuthMode();
    }
});

// Enhanced input navigation
document.querySelectorAll('.auth-input').forEach(input => {
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && this.type !== 'submit') {
            e.preventDefault();
            const form = this.closest('form');
            const inputs = Array.from(form.querySelectorAll('.auth-input'));
            const currentIndex = inputs.indexOf(this);
            const nextInput = inputs[currentIndex + 1];
            
            if (nextInput) {
                nextInput.focus();
            } else {
                form.querySelector('button[type="submit"]').click();
            }
        }
    });
});

// Add input animation effects
document.querySelectorAll('.input-wrapper').forEach(wrapper => {
    const input = wrapper.querySelector('.auth-input');
    
    wrapper.style.transition = 'transform 0.2s ease';
    
    input.addEventListener('focus', () => {
        wrapper.style.transform = 'translateY(-1px)';
    });
    
    input.addEventListener('blur', () => {
        wrapper.style.transform = 'translateY(0)';
    });
});

// Utility function to get current user info (if logged in)
async function getCurrentUser() {
    const token = getToken();
    if (!token) {
        return null;
    }
    
    try {
        const response = await makeAPIRequest('/auth/me', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        return response;
    } catch (error) {
        console.error('Failed to get current user:', error);
        clearToken();
        return null;
    }
}