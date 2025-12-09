/**
 * Contractor Vault - Content Script
 * Minimal content script - no storage access
 */

console.log('[ContractorVault] Content script loaded on', window.location.hostname);

// Content scripts cannot access chrome.storage.session
// All logic is handled by background.js
