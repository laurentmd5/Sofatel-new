// Gestionnaire de signatures complet avec enregistrement

// Configuration globale
const config = {
    autoSaveInterval: 120000, // 2 minutes
    toastDuration: 5000 // 5 secondes
};

// État global
const state = {
    isSubmitting: false,
    signaturePads: {
        survey: { equipe: null, client: null },
        intervention: { equipe: null, client: null },
        ficheTechnique: { equipe: null, client: null }
    }
};

// Initialisation principale
document.addEventListener('DOMContentLoaded', function() {
    initializeSignaturePads();
    setupFormHandlers();
    setupAutoSave();
    if (typeof window.safeFeatherReplace === 'function') window.safeFeatherReplace();
    else if (typeof feather !== 'undefined') feather.replace();
});

function initializeSignaturePads() {
    // Survey
    initPad('survey', 'equipe', '#signatureEquipeSurvey', 'signature_equipe');
    initPad('survey', 'client', '#signatureClientSurvey', 'signature_client');

    // Intervention
    initPad('intervention', 'equipe', '#signatureEquipe', 'signature_equipe');
    initPad('intervention', 'client', '#signatureClient', 'signature_client');

    // Fiche Technique
    initPad('ficheTechnique', 'equipe', '#signatureEquipeFT', 'signature_equipe');
    initPad('ficheTechnique', 'client', '#signatureClientFT', 'signature_client');
}

function initPad(category, name, canvasSelector, inputId) {
    const canvas = document.querySelector(canvasSelector);
    if (!canvas) return;

    // Configuration HD
    const ratio = Math.max(window.devicePixelRatio || 1, 1);
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    canvas.getContext('2d').scale(ratio, ratio);

    state.signaturePads[category][name] = new SignaturePad(canvas, {
        backgroundColor: 'rgb(255, 255, 255)',
        penColor: 'rgb(0, 0, 0)'
    });

    // Restauration signature existante
    const input = document.getElementById(inputId);
    if (input && input.value) {
        state.signaturePads[category][name].fromDataURL(input.value);
    }

    // Mise à jour automatique
    state.signaturePads[category][name].addEventListener('endStroke', () => {
        if (input) {
            input.value = state.signaturePads[category][name].isEmpty() 
                ? '' 
                : state.signaturePads[category][name].toDataURL();
        }
        hideFeedback(`${inputId}-feedback`);
    });
}

// Redimensionner les canvas quand ils deviennent visibles
function resizeSignaturePads(category = 'intervention') {
    const pads = state.signaturePads[category];
    if (!pads) return;

    const mapping = {
        equipe: { selector: '#signatureEquipe', inputId: 'signature_equipe' },
        client: { selector: '#signatureClient', inputId: 'signature_client' },
        survey_equipe: { selector: '#signatureEquipeSurvey', inputId: 'signature_equipe' },
        survey_client: { selector: '#signatureClientSurvey', inputId: 'signature_client' },
        ft_equipe: { selector: '#signatureEquipeFT', inputId: 'signature_equipe' },
        ft_client: { selector: '#signatureClientFT', inputId: 'signature_client' }
    };

    // Resize each pad
    ['equipe', 'client'].forEach(name => {
        if (pads[name]) {
            const pad = pads[name];
            const canvas = pad.canvas;
            
            const ratio = Math.max(window.devicePixelRatio || 1, 1);
            canvas.width = canvas.offsetWidth * ratio;
            canvas.height = canvas.offsetHeight * ratio;
            canvas.getContext('2d').scale(ratio, ratio);
            
            console.log(`✓ Resized ${category}.${name}: ${canvas.width}x${canvas.height}`);
        }
    });
}

function setupFormHandlers() {
    // Survey Form
    const surveyForm = document.getElementById('surveyForm');
    if (surveyForm && !surveyForm.dataset.noAjax) {
        surveyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!state.isSubmitting) {
                handleFormSubmit(this, 'survey');
            }
        });
    }

    // Intervention Form
    const interventionForm = document.getElementById('interventionForm');
    if (interventionForm) {
        interventionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!state.isSubmitting) {
                handleFormSubmit(this, 'intervention');
            }
        });
    }

    // Fiche Technique Form
    const ficheTechniqueForm = document.getElementById('ficheTechniqueForm');
    if (ficheTechniqueForm) {
        ficheTechniqueForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!state.isSubmitting) {
                handleFormSubmit(this, 'ficheTechnique');
            }
        });
    }
}

function handleFormSubmit(form, formType) {
    if (!validateForm(formType)) {
        showToast('Veuillez compléter tous les champs obligatoires', 'error');
        return;
    }

    state.isSubmitting = true;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalContent = submitBtn.innerHTML;

    // Afficher l'indicateur de chargement
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
        Envoi en cours...
    `;

    // Préparer les données
    const formData = new FormData(form);
    const endpoint = form.action;

    // Envoyer la requête
    fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(async response => {
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Réponse non-JSON reçue');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showToast(`${formType === 'survey' ? 'Survey' : 'Intervention'} enregistré avec succès`, 'success');
            if (data.redirect) {
                setTimeout(() => window.location.href = data.redirect, 1500);
            }
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast(error.message || 'Erreur lors de l\'enregistrement', 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalContent;
        state.isSubmitting = false;
    });
}

function validateForm(formType) {
    let isValid = true;
    const pads = state.signaturePads[formType];

    // Validation des signatures
    for (const [name, pad] of Object.entries(pads)) {
        if (pad && pad.isEmpty()) {
            const inputId = getInputId(formType, name);
            const feedbackElement = document.getElementById(`${inputId}-feedback`);
            if (feedbackElement) {
                feedbackElement.style.display = 'block';
            }
            isValid = false;
        }
    }

    // Validation des champs requis
    const requiredFields = Array.from(document.querySelectorAll('[required]'));
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

function getInputId(formType, padName) {
    const mapping = {
        survey: {
            equipe: 'signature_equipe',
            client: 'signature_client'
        },
        intervention: {
            equipe: 'signature_equipe',
            client: 'signature_client'
        },
        ficheTechnique: {
            equipe: 'signature_equipe',
            client: 'signature_client'
        }
    };
    return mapping[formType]?.[padName] || '';
}

function setupAutoSave() {
    setInterval(() => {
        const form = document.getElementById('interventionForm') || 
                     document.getElementById('surveyForm') || 
                     document.getElementById('ficheTechniqueForm');
        if (form) {
            autoSaveForm(form);
        }
    }, config.autoSaveInterval);
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const endpoint = `/auto-save-${form.id.replace('Form', '').toLowerCase()}/${form.dataset.interventionId || ''}`;

    fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Sauvegarde automatique effectuée');
        }
    })
    .catch(error => {
        console.error('Erreur sauvegarde auto:', error);
    });
}

// Fonction pour effacer une signature
window.clearSignature = function(type) {
    const [category, name] = parseSignatureType(type);
    const pad = state.signaturePads[category]?.[name];
    
    if (pad) {
        pad.clear();
        const inputId = getInputId(category, name);
        const input = document.getElementById(inputId);
        if (input) input.value = '';
    }
};

function parseSignatureType(type) {
    if (type.includes('Survey')) return ['survey', type.replace('Survey', '').toLowerCase()];
    if (type.includes('FT')) return ['ficheTechnique', type.replace('FT', '').toLowerCase()];
    return ['intervention', type.toLowerCase()];
}

function hideFeedback(feedbackId) {
    const feedbackElement = document.getElementById(feedbackId);
    if (feedbackElement) {
        feedbackElement.style.display = 'none';
    }
}

// Fonction pour afficher les notifications
window.showToast = function(message, type = 'info') {
    const toast = document.getElementById('toastNotification');
    const toastMessage = document.getElementById('toastMessage');
    
    if (!toast || !toastMessage) {
        console.warn('Éléments toast non trouvés');
        return;
    }
    
    toastMessage.textContent = message;
    toast.style.display = 'block';
    
    // Style selon le type
    const toastElement = toast.querySelector('.toast');
    toastElement.className = 'toast show ' + 
        (type === 'success' ? 'bg-success text-white' : 
         type === 'error' ? 'bg-danger text-white' : 
         'bg-info text-dark');
    
    // Masquer automatiquement
    setTimeout(() => {
        toast.style.display = 'none';
    }, config.toastDuration);
};

// Empêcher la perte de données
window.addEventListener('beforeunload', function(e) {
    const forms = ['interventionForm', 'surveyForm', 'ficheTechniqueForm']
        .map(id => document.getElementById(id))
        .filter(form => form !== null);
    
    if (forms.some(form => formHasChanges(form))) {
        e.preventDefault();
        e.returnValue = 'Vous avez des modifications non enregistrées. Voulez-vous vraiment quitter?';
    }
});

function formHasChanges(form) {
    // Implémentation basique - à adapter selon vos besoins
    return Array.from(new FormData(form).entries()).length > 0;
}