/**
 * @jest-environment jsdom
 *
 * Tests for frontend/script.js logic.
 *
 * script.js is a browser script (not a module), so these tests replicate
 * and verify the core pure functions in isolation using jsdom.
 */

// ── escapeHtml ────────────────────────────────────────────────────────────────
// Mirrors the escapeHtml function in script.js
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

describe('escapeHtml', () => {
    test('leaves plain text unchanged', () => {
        expect(escapeHtml('Hello world')).toBe('Hello world');
    });

    test('escapes < and > characters', () => {
        expect(escapeHtml('<script>')).toBe('&lt;script&gt;');
    });

    test('escapes & character', () => {
        expect(escapeHtml('a & b')).toBe('a &amp; b');
    });

    test('escapes a basic XSS attempt', () => {
        expect(escapeHtml('<img src=x onerror=alert(1)>')).toBe(
            '&lt;img src=x onerror=alert(1)&gt;'
        );
    });

    test('returns empty string for empty input', () => {
        expect(escapeHtml('')).toBe('');
    });
});

// ── createLoadingMessage ──────────────────────────────────────────────────────
// Mirrors the createLoadingMessage function in script.js
function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

describe('createLoadingMessage', () => {
    test('returns an element with class "message assistant"', () => {
        expect(createLoadingMessage().className).toBe('message assistant');
    });

    test('contains a .loading div with exactly 3 spans', () => {
        const el = createLoadingMessage();
        expect(el.querySelectorAll('.loading span')).toHaveLength(3);
    });

    test('wraps content inside .message-content', () => {
        const el = createLoadingMessage();
        expect(el.querySelector('.message-content')).not.toBeNull();
    });
});

// ── source link generation ────────────────────────────────────────────────────
// Mirrors the source-link mapping logic inside addMessage in script.js
function buildSourceLinks(sources) {
    return sources
        .map(s =>
            s.url
                ? `<a href="${s.url}" target="_blank" rel="noopener noreferrer">${s.text}</a>`
                : `<span>${s.text}</span>`
        )
        .join('');
}

describe('buildSourceLinks', () => {
    test('returns empty string for empty sources array', () => {
        expect(buildSourceLinks([])).toBe('');
    });

    test('renders an anchor tag when a URL is present', () => {
        const html = buildSourceLinks([{ text: 'Lesson 1', url: 'https://example.com' }]);
        expect(html).toContain('<a href="https://example.com"');
        expect(html).toContain('Lesson 1');
        expect(html).toContain('target="_blank"');
        expect(html).toContain('rel="noopener noreferrer"');
    });

    test('renders a span when URL is null', () => {
        const html = buildSourceLinks([{ text: 'Lesson 2', url: null }]);
        expect(html).toBe('<span>Lesson 2</span>');
    });

    test('handles a mix of sources with and without URLs', () => {
        const html = buildSourceLinks([
            { text: 'Source A', url: 'https://a.com' },
            { text: 'Source B', url: null },
        ]);
        expect(html).toContain('<a href="https://a.com"');
        expect(html).toContain('<span>Source B</span>');
    });
});
