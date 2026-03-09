/**
 * SOFATELCOM Toast Notification System
 * Modern, accessible toast notifications for user feedback
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'true');
            this.container.style.cssText = `
                position: fixed;
                top: 1.5rem;
                right: 1.5rem;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                max-width: 400px;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    show(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        const toastId = `toast-${Date.now()}`;
        toast.id = toastId;
        
        // Determine styles based on type
        const colors = {
            success: { bg: '#198754', icon: '✓' },
            error: { bg: '#dc3545', icon: '✕' },
            warning: { bg: '#ffc107', icon: '⚠' },
            info: { bg: '#0dcaf0', icon: 'ℹ' }
        };
        
        const color = colors[type] || colors.info;
        
        toast.setAttribute('role', 'status');
        toast.innerHTML = `
            <div style="
                background: white;
                border-radius: 8px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
                padding: 1rem 1.25rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                pointer-events: auto;
                border-left: 4px solid ${color.bg};
                max-width: 100%;
                word-wrap: break-word;
            ">
                <span style="
                    color: ${color.bg};
                    font-weight: bold;
                    font-size: 1.25rem;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 1.5rem;
                    height: 1.5rem;
                ">${color.icon}</span>
                <span style="
                    color: #212529;
                    font-size: 0.875rem;
                    flex: 1;
                    line-height: 1.4;
                ">${message}</span>
                <button style="
                    background: none;
                    border: none;
                    color: #6c757d;
                    cursor: pointer;
                    padding: 0;
                    font-size: 1.25rem;
                    flex-shrink: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 1.5rem;
                    height: 1.5rem;
                    transition: color 0.2s;
                " 
                onmouseover="this.style.color='#212529'"
                onmouseout="this.style.color='#6c757d'"
                onclick="document.getElementById('${toastId}').remove()">✕</button>
            </div>
        `;
        
        this.container.appendChild(toast);
        
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.style.animation = 'slideOutRight 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }
        
        return toastId;
    }

    success(message, duration = 4000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    remove(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) toast.remove();
    }

    clear() {
        this.container.innerHTML = '';
    }
}

// Create global instance
const Toast = new ToastManager();

// Add required animations to document if not already present
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(400px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(400px);
            }
        }
    `;
    document.head.appendChild(style);
}

// Expose for inline use
window.Toast = Toast;
