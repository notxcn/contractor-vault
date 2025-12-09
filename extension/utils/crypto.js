/**
 * Contractor Vault - Client-side Crypto Utilities
 * WebCrypto API wrapper for secure operations
 * 
 * Note: For MVP, actual decryption happens server-side.
 * This module is prepared for future client-side decryption.
 */

/**
 * Decode base64 to Uint8Array
 */
export function base64ToBytes(base64) {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
}

/**
 * Encode Uint8Array to base64
 */
export function bytesToBase64(bytes) {
    let binaryString = '';
    for (let i = 0; i < bytes.length; i++) {
        binaryString += String.fromCharCode(bytes[i]);
    }
    return btoa(binaryString);
}

/**
 * Derive an AES key from a password using PBKDF2
 * (For future use with client-side encryption)
 */
export async function deriveKey(password, salt) {
    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);

    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        passwordBuffer,
        'PBKDF2',
        false,
        ['deriveKey']
    );

    return crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: salt,
            iterations: 100000,
            hash: 'SHA-256',
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['decrypt']
    );
}

/**
 * Decrypt data using AES-GCM
 * (For future use with client-side decryption)
 */
export async function decrypt(key, iv, ciphertext) {
    const decrypted = await crypto.subtle.decrypt(
        {
            name: 'AES-GCM',
            iv: iv,
        },
        key,
        ciphertext
    );

    return new TextDecoder().decode(decrypted);
}

/**
 * Parse a Fernet token (for future client-side decryption)
 * Fernet format: Version (1 byte) | Timestamp (8 bytes) | IV (16 bytes) | Ciphertext | HMAC (32 bytes)
 */
export function parseFernetToken(tokenBase64) {
    const bytes = base64ToBytes(tokenBase64.replace(/-/g, '+').replace(/_/g, '/'));

    if (bytes.length < 57) {
        throw new Error('Invalid Fernet token');
    }

    const version = bytes[0];
    if (version !== 0x80) {
        throw new Error('Unsupported Fernet version');
    }

    const timestamp = bytes.slice(1, 9);
    const iv = bytes.slice(9, 25);
    const ciphertext = bytes.slice(25, -32);
    const hmac = bytes.slice(-32);

    return { version, timestamp, iv, ciphertext, hmac };
}
