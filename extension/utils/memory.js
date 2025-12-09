/**
 * Contractor Vault - Secure Memory Utilities
 * Best-effort memory cleanup for sensitive data
 * 
 * Note: JavaScript's garbage collection makes true memory zeroing impossible.
 * These utilities provide best-effort cleanup by overwriting and dereferencing.
 */

/**
 * Overwrite a string with zeros and return null
 * This doesn't truly erase the original string (immutable in JS),
 * but it removes the reference as quickly as possible.
 * 
 * @param {string} sensitiveString - The string to "zero"
 * @returns {null} - Always returns null
 */
export function zeroString(sensitiveString) {
    if (typeof sensitiveString !== 'string') {
        return null;
    }

    // Create overwrite string (won't affect original, but clears reference)
    const length = sensitiveString.length;

    // Overwrite with zeros in a new variable
    let zeroed = '0'.repeat(length);

    // Clear the zeroed string too
    zeroed = null;

    return null;
}

/**
 * Zero out a Uint8Array in place
 * This actually modifies the array contents.
 * 
 * @param {Uint8Array} buffer - The buffer to zero
 */
export function zeroBuffer(buffer) {
    if (!(buffer instanceof Uint8Array)) {
        return;
    }

    // Fill with zeros
    buffer.fill(0);

    // Double-pass with random values then zeros (paranoid mode)
    crypto.getRandomValues(buffer);
    buffer.fill(0);
}

/**
 * Zero out an object's properties
 * Overwrites string and buffer properties.
 * 
 * @param {Object} obj - Object with sensitive properties
 * @param {string[]} properties - Array of property names to zero
 */
export function zeroObject(obj, properties) {
    if (!obj || typeof obj !== 'object') {
        return;
    }

    for (const prop of properties) {
        if (obj.hasOwnProperty(prop)) {
            const value = obj[prop];

            if (typeof value === 'string') {
                // Overwrite with zeros
                obj[prop] = '0'.repeat(value.length);
                obj[prop] = null;
            } else if (value instanceof Uint8Array) {
                zeroBuffer(value);
                obj[prop] = null;
            } else {
                obj[prop] = null;
            }
        }
    }
}

/**
 * Create a secure container for sensitive data
 * Provides automatic cleanup after use.
 * 
 * @param {*} data - Sensitive data to contain
 * @param {number} ttlMs - Time-to-live in milliseconds
 * @returns {Object} - Container with read() and destroy() methods
 */
export function createSecureContainer(data, ttlMs = 30000) {
    let _data = data;
    let _destroyed = false;

    // Auto-destroy after TTL
    const timer = setTimeout(() => {
        destroy();
    }, ttlMs);

    function destroy() {
        if (_destroyed) return;

        clearTimeout(timer);

        if (typeof _data === 'string') {
            _data = '0'.repeat(_data.length);
        } else if (_data instanceof Uint8Array) {
            zeroBuffer(_data);
        }

        _data = null;
        _destroyed = true;
    }

    return {
        read() {
            if (_destroyed) {
                throw new Error('Container has been destroyed');
            }
            return _data;
        },
        destroy,
        isDestroyed() {
            return _destroyed;
        },
    };
}
