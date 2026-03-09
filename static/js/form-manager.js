/**
 * SOFATELCOM Form Manager
 * Enhanced form handling with validation, loading states, and toasts
 */

class FormManager {
    constructor(formSelector) {
        this.form = document.querySelector(formSelector);
        if (!this.form) throw new Error(`Form not found: ${formSelector}`);
        
        this.submitBtn = this.form.querySelector('[type="submit"]');
        this.isSubmitting = false;
        this.init();
    }

    init() {
        // Add loading state to submit button on form submission
        this.form.addEventListener('submit', (e) => {
            if (!this.form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                this.markInvalid();
                Toast.warning('Veuillez corriger les erreurs du formulaire');
                return;
            }
            
            // Set loading state only for non-file uploads with no fetch intercept
            if (this.submitBtn && !this.form.hasAttribute('data-no-loading')) {
                this.setLoading(true);
            }
        });

        // Handle AJAX form submission if data-ajax="true"
        if (this.form.hasAttribute('data-ajax')) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitAjax();
            });
        }

        // Reset loading state on unload (back button, etc)
        window.addEventListener('beforeunload', () => {
            if (this.submitBtn) this.setLoading(false);
        });
    }

    async submitAjax() {
        if (!this.form.checkValidity()) {
            this.markInvalid();
            Toast.warning('Veuillez corriger les erreurs du formulaire');
            return;
        }

        this.clearErrors();
        this.setLoading(true);

        try {
            const formData = new FormData(this.form);
            const method = this.form.method.toUpperCase() || 'POST';
            const action = this.form.action || window.location.href;

            const response = await fetch(action, {
                method: method,
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (response.ok) {
                Toast.success(data.message || 'Opération réussie!');
                
                // Reset form if requested
                if (this.form.hasAttribute('data-reset-on-success')) {
                    this.form.reset();
                }

                // Redirect if specified
                if (data.redirect) {
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 500);
                }

                // Trigger custom success event
                this.form.dispatchEvent(new CustomEvent('submit-success', { detail: data }));
            } else {
                // Handle field errors
                if (data.errors) {
                    this.displayErrors(data.errors);
                    Toast.error(data.message || 'Veuillez corriger les erreurs');
                } else {
                    Toast.error(data.message || 'Une erreur s\'est produite');
                }
            }
        } catch (error) {
            console.error('Form submission error:', error);
            Toast.error('Erreur réseau: ' + error.message);
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(isLoading) {
        if (!this.submitBtn) return;

        this.isSubmitting = isLoading;
        this.submitBtn.disabled = isLoading;
        this.submitBtn.setAttribute('data-loading', isLoading);

        if (isLoading) {
            this.submitBtn.setAttribute('data-original-text', this.submitBtn.textContent);
            // Text will be hidden by CSS, spinner shown
        } else {
            const originalText = this.submitBtn.getAttribute('data-original-text');
            if (originalText) {
                this.submitBtn.textContent = originalText;
                this.submitBtn.removeAttribute('data-original-text');
            }
        }
    }

    displayErrors(errors) {
        Object.keys(errors).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('is-invalid');
                
                // Remove old error message
                const oldError = field.parentElement.querySelector('.invalid-feedback');
                if (oldError) oldError.remove();

                // Add new error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback d-block';
                errorDiv.textContent = Array.isArray(errors[fieldName]) 
                    ? errors[fieldName][0] 
                    : errors[fieldName];
                
                field.parentElement.appendChild(errorDiv);
            }
        });
    }

    clearErrors() {
        this.form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        this.form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
    }

    markInvalid() {
        this.form.classList.add('was-validated');
    }

    // Utility methods
    getValue(fieldName) {
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        return field ? field.value : null;
    }

    setValue(fieldName, value) {
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.value = value;
            field.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    reset() {
        this.form.reset();
        this.clearErrors();
        this.form.classList.remove('was-validated');
    }

    disable() {
        this.form.querySelectorAll('input, select, textarea, button').forEach(el => {
            el.disabled = true;
        });
    }

    enable() {
        this.form.querySelectorAll('input, select, textarea, button').forEach(el => {
            el.disabled = false;
        });
    }
}

/**
 * Initialize all forms with data-form attribute
 */
function initializeForms() {
    document.querySelectorAll('form[data-form]').forEach(form => {
        const formName = form.getAttribute('data-form');
        window[`form_${formName}`] = new FormManager(`form[data-form="${formName}"]`);
    });
}

/**
 * Initialize form validation in real-time
 */
function initializeRealTimeValidation() {
    document.querySelectorAll('.form-control, .form-check-input').forEach(field => {
        field.addEventListener('blur', () => {
            if (field.form && field.form.classList.contains('was-validated')) {
                field.form.classList.add('was-validated');
            }
        });

        if (field.classList.contains('form-control')) {
            field.addEventListener('input', () => {
                if (field.classList.contains('is-invalid')) {
                    field.classList.remove('is-invalid');
                    const error = field.parentElement.querySelector('.invalid-feedback');
                    if (error) error.remove();
                }
            });
        }
    });
}

/**
 * Handle file input preview
 */
function initializeFileInputs() {
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            const files = this.files;
            if (files.length > 0) {
                const fileNames = Array.from(files).map(f => f.name).join(', ');
                const label = this.parentElement.querySelector('.file-count');
                if (label) {
                    label.textContent = `${files.length} fichier(s) sélectionné(s): ${fileNames}`;
                }
            }
        });
    });
}

/**
 * Initialize password strength indicator
 */
function initializePasswordStrength() {
    document.querySelectorAll('input[type="password"][data-strength]').forEach(input => {
        const indicator = input.parentElement.querySelector('.password-strength');
        if (!indicator) return;

        input.addEventListener('input', () => {
            const strength = calculatePasswordStrength(input.value);
            updateStrengthIndicator(indicator, strength);
        });
    });
}

function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    return Math.min(strength, 4);
}

function updateStrengthIndicator(indicator, strength) {
    const levels = ['', 'weak', 'fair', 'good', 'strong'];
    const colors = ['', 'danger', 'warning', 'info', 'success'];
    
    indicator.className = 'password-strength';
    if (strength > 0) {
        indicator.classList.add(`strength-${levels[strength]}`);
        indicator.innerHTML = `
            <div class="progress" style="height: 4px;">
                <div class="progress-bar bg-${colors[strength]}" style="width: ${(strength / 4) * 100}%"></div>
            </div>
            <small class="text-${colors[strength]} fw-medium">${levels[strength].toUpperCase()}</small>
        `;
    }
}

/**
 * Initialize character counter for textarea/input
 */
function initializeCharacterCounters() {
    document.querySelectorAll('[maxlength][data-counter]').forEach(field => {
        const maxLength = field.maxLength;
        const counter = field.parentElement.querySelector('.char-counter');
        
        if (counter) {
            const updateCounter = () => {
                const remaining = maxLength - field.value.length;
                counter.textContent = `${field.value.length}/${maxLength}`;
                counter.classList.toggle('text-danger', remaining < 10);
            };

            field.addEventListener('input', updateCounter);
            updateCounter();
        }
    });
}

// Initialize all form enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeForms();
    initializeRealTimeValidation();
    initializeFileInputs();
    initializePasswordStrength();
    initializeCharacterCounters();
});

// Expose to window for manual use
window.FormManager = FormManager;

/* ============================================================================
   FORM STEP MANAGER - Multi-step form with validation
   ============================================================================ */

class FormStepManager {
    constructor(formSelector = '#intervention-form', options = {}) {
        this.form = document.querySelector(formSelector);
        if (!this.form) {
            console.error(`❌ Form not found: ${formSelector}`);
            return;
        }

        this.currentStep = 1;
        this.totalSteps = this.form.querySelectorAll('[data-step]').length;
        this.validationRules = new Map();
        
        // Options
        this.options = {
            autoFocus: options.autoFocus ?? true,
            saveProgress: options.saveProgress ?? true,
            allowSkip: options.allowSkip ?? false,
            ...options
        };

        this.init();
    }

    init() {
        console.log(`✅ FormStepManager initialized (${this.totalSteps} steps)`);
        this.updateProgressIndicator();
        this.attachEventListeners();
        this.loadProgressFromStorage();
        this.showStep(this.currentStep);
    }

    attachEventListeners() {
        const prevBtn = this.form.querySelector('[data-prev-step]');
        const nextBtn = this.form.querySelector('[data-next-step]');
        const submitBtn = this.form.querySelector('[data-submit-form]');

        if (prevBtn) prevBtn.addEventListener('click', () => this.previousStep());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextStep());
        if (submitBtn) submitBtn.addEventListener('click', (e) => this.submit(e));

        // Real-time validation
        this.form.querySelectorAll('[required], [data-validate]').forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('change', () => this.validateField(field));
        });

        // Click on step indicators
        document.querySelectorAll('[data-step-indicator]').forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                const stepNumber = parseInt(indicator.dataset.stepIndicator);
                if (this.isStepAccessible(stepNumber)) {
                    this.goToStep(stepNumber);
                }
            });
        });

        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submit(e);
        });
    }

    showStep(stepNumber) {
        this.form.querySelectorAll('[data-step]').forEach(step => {
            step.classList.remove('active');
        });

        const targetStep = this.form.querySelector(`[data-step="${stepNumber}"]`);
        if (targetStep) {
            targetStep.classList.add('active');
            if (this.options.autoFocus) {
                const firstInput = targetStep.querySelector('input, textarea, select');
                if (firstInput) setTimeout(() => firstInput.focus(), 100);
            }
        }

        this.updateProgressIndicator();
        this.updateActionButtons();
    }

    goToStep(stepNumber) {
        if (stepNumber < 1 || stepNumber > this.totalSteps) return false;
        this.currentStep = stepNumber;
        this.showStep(stepNumber);
        return true;
    }

    nextStep() {
        if (!this.validateCurrentStep()) {
            this.scrollToFirstError();
            return false;
        }

        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.showStep(this.currentStep);
            window.scrollTo({ top: 0, behavior: 'smooth' });
            this.saveProgress();
            return true;
        }
        return false;
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.showStep(this.currentStep);
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return true;
        }
        return false;
    }

    validateCurrentStep() {
        const currentStepElement = this.form.querySelector(`[data-step="${this.currentStep}"]`);
        if (!currentStepElement) return false;

        let isValid = true;
        const requiredFields = currentStepElement.querySelectorAll('[required], [data-validate]');

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateField(field) {
        const value = field.value?.trim() || '';
        let error = null;

        if (field.hasAttribute('required') && !value) {
            error = 'Champ obligatoire';
        }

        if (!error) {
            const type = field.getAttribute('data-validate') || field.type;
            error = this.validateByType(value, type, field);
        }

        if (!error && this.validationRules.has(field.name)) {
            const rule = this.validationRules.get(field.name);
            error = rule(value, field);
        }

        this.displayFieldError(field, error);
        return !error;
    }

    validateByType(value, type, field) {
        if (!value) return null;

        switch (type) {
            case 'email':
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? null : 'Email invalide';
            
            case 'phone':
            case 'tel':
                return /^(?:\+221|0)?[1-9]\d{8}$/.test(value.replace(/[\s\-\(\)]/g, '')) ? null : 'Téléphone invalide';
            
            case 'number':
                return !isNaN(value) && value !== '' ? null : 'Doit être un nombre';
            
            case 'date':
                return new Date(value) instanceof Date ? null : 'Date invalide';
            
            case 'gps':
                const parts = value.replace(/\s/g, '').split(/[,;]/);
                if (parts.length === 2) {
                    const [lat, lon] = parts.map(p => parseFloat(p));
                    return lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180 ? null : 'GPS invalide';
                }
                return 'Format GPS: lat,lon';
            
            default:
                return null;
        }
    }

    displayFieldError(field, error) {
        const formGroup = field.closest('.form-group') || field.parentElement;
        let errorElement = formGroup?.querySelector('.invalid-feedback');

        if (error) {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');

            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'invalid-feedback';
                formGroup.appendChild(errorElement);
            }

            errorElement.textContent = error;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');

            if (errorElement) {
                errorElement.remove();
            }
        }
    }

    updateProgressIndicator() {
        const indicators = document.querySelectorAll('[data-step-indicator]');
        const progressFill = document.querySelector('.form-progress-fill');

        indicators.forEach((indicator, index) => {
            const stepNumber = index + 1;
            indicator.classList.remove('active', 'completed');

            if (stepNumber === this.currentStep) {
                indicator.classList.add('active');
            } else if (stepNumber < this.currentStep) {
                indicator.classList.add('completed');
            }
        });

        if (progressFill) {
            const progressPercent = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100;
            progressFill.style.width = `${progressPercent}%`;
        }
    }

    updateActionButtons() {
        const prevBtn = this.form.querySelector('[data-prev-step]');
        const nextBtn = this.form.querySelector('[data-next-step]');
        const submitBtn = this.form.querySelector('[data-submit-form]');

        if (prevBtn) prevBtn.disabled = this.currentStep === 1;
        if (nextBtn) nextBtn.style.display = this.currentStep < this.totalSteps ? 'block' : 'none';
        if (submitBtn) submitBtn.style.display = this.currentStep === this.totalSteps ? 'block' : 'none';
    }

    async submit(e) {
        e?.preventDefault();

        if (!this.validateCurrentStep()) {
            this.scrollToFirstError();
            return false;
        }

        const submitBtn = this.form.querySelector('[data-submit-form]');
        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
        }

        try {
            const formData = new FormData(this.form);
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (response.ok) {
                console.log('✅ Form submitted successfully');
                this.clearProgress();
                setTimeout(() => {
                    window.location.href = response.url || '/';
                }, 1500);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Submission error:', error);
            Toast.error('Erreur lors de la soumission');
        } finally {
            if (submitBtn) {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
        }
    }

    isStepAccessible(stepNumber) {
        return stepNumber < this.currentStep || stepNumber === this.currentStep || this.options.allowSkip;
    }

    saveProgress() {
        if (!this.options.saveProgress) return;
        const data = { currentStep: this.currentStep, timestamp: new Date().toISOString() };
        localStorage.setItem(`form_progress_${this.form.id}`, JSON.stringify(data));
    }

    loadProgressFromStorage() {
        if (!this.options.saveProgress) return;
        const saved = localStorage.getItem(`form_progress_${this.form.id}`);
        if (saved) {
            try {
                const { currentStep } = JSON.parse(saved);
                this.currentStep = currentStep;
            } catch (e) {}
        }
    }

    clearProgress() {
        localStorage.removeItem(`form_progress_${this.form.id}`);
    }

    scrollToFirstError() {
        const firstError = this.form.querySelector('.is-invalid');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
    }

    addValidationRule(fieldName, validatorFn) {
        this.validationRules.set(fieldName, validatorFn);
    }
}

window.FormStepManager = FormStepManager;
