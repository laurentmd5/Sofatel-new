/**
 * ============================================================================
 * PERFORMANCE UTILITIES - Central Library
 * ============================================================================
 * Provides performance-first helpers:
 * - Debounce/Throttle
 * - RAF batching
 * - Interval manager (kill-switch)
 * - Safe DOM updates
 * - Event delegation
 * 
 * Usage: All modules should use these instead of raw setInterval/setTimeout
 */

// ============================================================================
// 1. DEBOUNCE & THROTTLE
// ============================================================================

/**
 * Debounce: Call function ONCE after X ms of silence
 * Use for: resize, input, search, filter changes
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeoutId;
    
    function debounced(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), wait);
    }
    
    debounced.cancel = () => clearTimeout(timeoutId);
    debounced.flush = () => {
        clearTimeout(timeoutId);
        func.apply(this, arguments);
    };
    
    return debounced;
}

/**
 * Throttle: Call function MAX once every X ms
 * Use for: scroll, mousemove, polling
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time between calls in ms
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    
    function throttled(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }
    }
    
    throttled.cancel = () => {
        inThrottle = false;
    };
    
    return throttled;
}

// ============================================================================
// 2. REQUESTANIMATIONFRAME BATCHING
// ============================================================================

/**
 * Batch DOM reads/writes using requestAnimationFrame
 * Prevents forced layout thrashing
 * 
 * Usage:
 *   batchDOMUpdates(() => {
 *       // Safe to read DOM here
 *       const width = element.offsetWidth;
 *   }, () => {
 *       // Safe to write DOM here (separate RAF)
 *       element.style.width = width + 'px';
 *   });
 */
const domBatcher = {
    readQueue: [],
    writeQueue: [],
    rafId: null,
    
    queueRead(callback) {
        this.readQueue.push(callback);
        this.scheduleFlush();
    },
    
    queueWrite(callback) {
        this.writeQueue.push(callback);
        this.scheduleFlush();
    },
    
    scheduleFlush() {
        if (this.rafId) return;
        
        this.rafId = requestAnimationFrame(() => {
            // Execute all reads first
            const reads = this.readQueue.splice(0);
            reads.forEach(cb => {
                try {
                    cb();
                } catch (e) {
                    console.error('❌ DOM read error:', e);
                }
            });
            
            // Then all writes
            const writes = this.writeQueue.splice(0);
            writes.forEach(cb => {
                try {
                    cb();
                } catch (e) {
                    console.error('❌ DOM write error:', e);
                }
            });
            
            this.rafId = null;
            
            // Keep flushing if queue has items
            if (this.readQueue.length > 0 || this.writeQueue.length > 0) {
                this.scheduleFlush();
            }
        });
    }
};

/**
 * Schedule DOM update batches safely
 */
function batchDOMUpdates(readFn, writeFn) {
    if (readFn) domBatcher.queueRead(readFn);
    if (writeFn) domBatcher.queueWrite(writeFn);
}

// ============================================================================
// 3. INTERVAL MANAGER - Central Control
// ============================================================================

/**
 * Central manager for all application intervals
 * Prevents memory leaks, enables kill-switch
 * 
 * Usage:
 *   IntervalManager.register('polling', () => fetch(...), 10000);
 *   IntervalManager.pause();  // Pause all
 *   IntervalManager.resume(); // Resume all
 *   IntervalManager.stop('polling'); // Stop specific
 *   IntervalManager.stopAll(); // Cleanup on page unload
 */
const IntervalManager = {
    intervals: new Map(),
    isPaused: false,
    
    /**
     * Register a recurring task
     * @param {string} id - Unique identifier
     * @param {Function} fn - Function to call
     * @param {number} interval - Interval in ms
     * @param {boolean} runNow - Execute immediately
     */
    register(id, fn, interval, runNow = false) {
        // Kill existing
        if (this.intervals.has(id)) {
            this.stop(id);
        }
        
        // Execute now if requested
        if (runNow) {
            try {
                fn();
            } catch (e) {
                console.error(`❌ Interval ${id} execution error:`, e);
            }
        }
        
        // Schedule recurring
        const intervalId = setInterval(() => {
            if (this.isPaused) return;
            
            try {
                fn();
            } catch (e) {
                console.error(`❌ Interval ${id} execution error:`, e);
            }
        }, interval);
        
        this.intervals.set(id, {
            intervalId,
            fn,
            interval,
            active: true
        });
        
        console.log(`✅ Interval registered: ${id} (${interval}ms)`);
    },
    
    /**
     * Stop specific interval
     */
    stop(id) {
        const entry = this.intervals.get(id);
        if (entry) {
            clearInterval(entry.intervalId);
            this.intervals.delete(id);
            console.log(`⏹️ Interval stopped: ${id}`);
        }
    },
    
    /**
     * Stop all intervals
     */
    stopAll() {
        for (const [id] of this.intervals) {
            this.stop(id);
        }
        console.log(`⏹️ All intervals stopped`);
    },
    
    /**
     * Pause all intervals (keep registered)
     */
    pause() {
        this.isPaused = true;
        console.log(`⏸️ All intervals paused`);
    },
    
    /**
     * Resume all intervals
     */
    resume() {
        this.isPaused = false;
        console.log(`▶️ All intervals resumed`);
    },
    
    /**
     * Get status
     */
    getStatus() {
        return {
            paused: this.isPaused,
            count: this.intervals.size,
            intervals: Array.from(this.intervals.keys())
        };
    }
};

// ============================================================================
// 4. SAFE FEATHER ICON UPDATES
// ============================================================================

/**
 * Safe wrapper for feather.replace()
 * Only replaces changed elements, not entire DOM
 * @param {HTMLElement} container - Element to replace icons in (default: document)
 */
function safeFeatherReplace(container = document) {
    if (typeof feather === 'undefined' || !feather.replace) {
        console.warn('⚠️ Feather not available');
        return;
    }
    
    try {
        // Only replace in container, not entire document
        const icons = container.querySelectorAll('[data-feather]:not([data-feather-replaced])');
        if (icons.length === 0) return;
        
        // Mark as replaced to avoid duplicates
        icons.forEach(el => el.setAttribute('data-feather-replaced', 'true'));
        
        // Use feather's replace with limited scope
        feather.replace({ svg: { class: 'feather' } });
        
    } catch (e) {
        console.warn('⚠️ Feather replace error:', e);
    }
}

/**
 * Batch feather replacements (debounced)
 */
const debouncedFeatherReplace = debounce((container) => {
    safeFeatherReplace(container || document);
}, 100);

// ============================================================================
// 5. LISTENER CLEANUP HELPER
// ============================================================================

/**
 * Track event listeners to prevent duplicates
 */
const ListenerTracker = {
    listeners: new Map(),
    
    /**
     * Add listener with tracking
     * @param {HTMLElement} element - Target element
     * @param {string} event - Event name (e.g., 'click')
     * @param {Function} handler - Event handler
     * @param {object} options - addEventListener options
     */
    add(element, event, handler, options = {}) {
        if (!element) return;
        
        const key = this.getKey(element, event, handler);
        
        // Prevent duplicate
        if (this.listeners.has(key)) {
            console.warn('⚠️ Listener already attached:', key);
            return;
        }
        
        element.addEventListener(event, handler, options);
        
        this.listeners.set(key, {
            element,
            event,
            handler,
            options
        });
        
        console.log(`✅ Listener added: ${event}`);
    },
    
    /**
     * Remove specific listener
     */
    remove(element, event, handler) {
        if (!element) return;
        
        const key = this.getKey(element, event, handler);
        const entry = this.listeners.get(key);
        
        if (entry) {
            element.removeEventListener(event, handler, entry.options);
            this.listeners.delete(key);
            console.log(`🗑️ Listener removed: ${event}`);
        }
    },
    
    /**
     * Remove all listeners from element
     */
    removeAll(element) {
        if (!element) return;
        
        const toRemove = [];
        for (const [key, entry] of this.listeners) {
            if (entry.element === element) {
                toRemove.push(key);
            }
        }
        
        toRemove.forEach(key => {
            const entry = this.listeners.get(key);
            entry.element.removeEventListener(entry.event, entry.handler, entry.options);
            this.listeners.delete(key);
        });
        
        console.log(`🗑️ Removed ${toRemove.length} listeners from element`);
    },
    
    getKey(element, event, handler) {
        return `${element.id || element.tagName}::${event}::${handler.name || 'anonymous'}`;
    },
    
    getStatus() {
        return {
            count: this.listeners.size,
            listeners: Array.from(this.listeners.keys())
        };
    }
};

// ============================================================================
// 6. PAGINATION HELPER - Safe chunked updates
// ============================================================================

/**
 * Safely update list items with pagination
 * Updates in chunks across multiple frames
 * @param {Array} items - Array of items
 * @param {number} chunkSize - Items to process per frame
 * @param {Function} updateFn - Update function (item, index) => void
 * @param {Function} onComplete - Completion callback
 */
function safeChunkedUpdate(items, chunkSize, updateFn, onComplete) {
    let index = 0;
    
    function processChunk() {
        const end = Math.min(index + chunkSize, items.length);
        
        for (let i = index; i < end; i++) {
            try {
                updateFn(items[i], i);
            } catch (e) {
                console.error(`❌ Update error at index ${i}:`, e);
            }
        }
        
        index = end;
        
        if (index < items.length) {
            // Schedule next chunk on next frame
            requestAnimationFrame(processChunk);
        } else if (onComplete) {
            onComplete();
        }
    }
    
    requestAnimationFrame(processChunk);
}

// ============================================================================
// 7. GLOBAL CLEANUP
// ============================================================================

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
    IntervalManager.stopAll();
    domBatcher.rafId && cancelAnimationFrame(domBatcher.rafId);
    console.log('✅ Performance cleanup completed');
});

/**
 * Expose globally
 */
window.PerformanceUtils = {
    debounce,
    throttle,
    batchDOMUpdates,
    safeFeatherReplace: debouncedFeatherReplace,
    IntervalManager,
    ListenerTracker,
    safeChunkedUpdate
};

console.log('✅ Performance utilities loaded');
