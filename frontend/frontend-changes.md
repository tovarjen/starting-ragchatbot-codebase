# Frontend Changes

## Dark / Light Mode Toggle Button

### Feature summary
A fixed-position theme toggle button was added to the top-right corner of the UI.
Clicking it switches between the existing dark theme and a new light theme, with the
preference persisted to `localStorage` across page reloads.

---

### Files changed

#### `index.html`
- Added a `<button id="themeToggle" class="theme-toggle">` element directly inside
  `<body>`, before `.container`, so it renders above all other content.
- The button contains two inline SVGs:
  - `.icon-sun` — shown in dark mode; clicking switches to light.
  - `.icon-moon` — shown in light mode; clicking switches to dark.
- Accessibility: `aria-label` is set to the *next* action ("Switch to light mode" /
  "Switch to dark mode") and updated dynamically by JS. `title` provides a tooltip.
  The button is a native `<button>` so it is keyboard-focusable and activatable with
  Space/Enter by default.
- Cache-busting version bumped: `style.css?v=11`, `script.js?v=10`.

#### `style.css`
- **Light mode variables** — a `[data-theme="light"]` selector block overrides all
  CSS custom properties defined in `:root` with light-palette equivalents:
  - `--background: #f8fafc`, `--surface: #e2e8f0`, `--surface-hover: #cbd5e1`
  - `--text-primary: #0f172a`, `--text-secondary: #475569`
  - `--border-color: #cbd5e1`, `--assistant-message: #e2e8f0`
  - `--welcome-bg: #dbeafe`
  - Two new tokens `--toggle-bg` and `--toggle-border` control the button's own
    background so it always stands out in both themes.
- **`body` transition** — `transition: background-color 0.3s ease, color 0.3s ease`
  added so the whole-page colour change is smooth.
- **`.theme-toggle` styles** — circular 40×40 px button, `position: fixed` top-right,
  `z-index: 1000`. Hover lifts with `scale(1.1)` and shows a blue focus ring; active
  state scales down to 0.95 for tactile feedback.
- **Icon visibility** — `.icon-sun` is `display: block` by default (dark mode);
  `.icon-moon` is `display: none`. `[data-theme="light"]` flips them.
- **`@keyframes iconSpin`** — a subtle 30° rotate-in animation plays each time an
  icon becomes visible, giving the toggle a polished feel.
- **Transition list** — key structural elements (sidebar, chat area, messages, input,
  buttons) all receive `transition: background-color 0.3s ease, border-color 0.3s ease,
  color 0.3s ease` so the theme crossfade is smooth rather than a hard flash.

#### `script.js`
- **`initTheme()`** — called on `DOMContentLoaded`; reads `localStorage.getItem('theme')`
  and applies a saved light preference before the first paint (prevents flash).
- **`applyTheme(theme)`** — sets / removes the `data-theme` attribute on
  `document.documentElement`, updates the button's `aria-label` to reflect the *next*
  action, and saves the preference to `localStorage`.
- **`toggleTheme()`** — reads current theme from `document.documentElement` and calls
  `applyTheme` with the opposite value.
- **`setupEventListeners()`** — wired `click` on `#themeToggle` to `toggleTheme`.

---

### Design decisions
| Decision | Rationale |
|---|---|
| `data-theme` on `<html>` | Allows CSS variables to cascade to every element without extra class management |
| Sun = dark mode, Moon = light mode | Matches common convention: sun icon means "switch to light", moon means "switch to dark" |
| `localStorage` persistence | Zero-dependency, synchronous, works with the plain HTML/JS stack |
| `initTheme()` before render | Avoids a visible flash of dark→light on page load for light-mode users |
| Native `<button>` element | Free keyboard focus, Space/Enter activation, and ARIA role without extra attributes |

---

## Light Theme CSS Variables (full accessibility pass)

### Feature summary
Completed and hardened the light theme by extracting all remaining hardcoded colours
into CSS custom properties and adding WCAG AA–compliant light-mode overrides.

### Files changed

#### `style.css`

**New variables added to `:root` (dark-mode defaults)**

| Variable | Value | Usage |
|---|---|---|
| `--source-link-color` | `#a8c0ff` | Source chip link text |
| `--source-link-hover-color` | `#c5d5ff` | Source chip link hover text |
| `--source-span-color` | `#8ba3d4` | Source chip plain-text span |
| `--source-link-bg` | `rgba(37,99,235,0.1)` | Source chip background |
| `--source-link-border` | `rgba(37,99,235,0.2)` | Source chip border |
| `--source-link-hover-bg` | `rgba(37,99,235,0.2)` | Source chip hover background |
| `--source-link-hover-border` | `rgba(37,99,235,0.45)` | Source chip hover border |
| `--code-bg` | `rgba(0,0,0,0.2)` | Inline code / pre block background |
| `--error-color` | `#f87171` | Error message text |
| `--error-bg` | `rgba(239,68,68,0.1)` | Error message background |
| `--error-border` | `rgba(239,68,68,0.2)` | Error message border |
| `--success-color` | `#4ade80` | Success message text |
| `--success-bg` | `rgba(34,197,94,0.1)` | Success message background |
| `--success-border` | `rgba(34,197,94,0.2)` | Success message border |

**Light-mode overrides in `[data-theme="light"]`**

All overrides pass WCAG AA (≥4.5:1 contrast ratio for normal text):

| Variable | Light value | Contrast vs `#f8fafc` |
|---|---|---|
| `--surface` | `#ffffff` | — (background) |
| `--surface-hover` | `#e2e8f0` | — (background) |
| `--assistant-message` | `#ffffff` | — (background) |
| `--source-link-color` | `#1d4ed8` (blue-700) | ~6.8:1 ✓ |
| `--source-link-hover-color` | `#1e40af` (blue-800) | ~8.3:1 ✓ |
| `--source-span-color` | `#475569` (slate-600) | ~5.9:1 ✓ |
| `--error-color` | `#b91c1c` (red-700) | ~5.5:1 ✓ |
| `--success-color` | `#15803d` (green-700) | ~5.4:1 ✓ |
| `--code-bg` | `rgba(0,0,0,0.05)` | — (tint) |

**Hardcoded colours replaced with variables**
- `.sources-content a, .sources-content span` — all colour, bg, and border values now use variables
- `.sources-content a:hover` — hover colour now uses variable
- `.message-content code`, `.message-content pre` — `rgba(0,0,0,0.2)` → `var(--code-bg)`
- `.error-message` — all three colour properties → variables
- `.success-message` — all three colour properties → variables

**Bug fixed**
- `.message-content blockquote` referenced `var(--primary)` which was undefined.
  Corrected to `var(--primary-color)`.

**Cache-busting**: `style.css?v=12`

---

## JavaScript Theme Toggle — Smooth Transitions & OS Detection

### Feature summary
Hardened the JS theme logic to eliminate the initial-paint flash, detect the OS colour
scheme as a default, and respect the `prefers-reduced-motion` accessibility setting.

### Files changed

#### `script.js` (`v=11`)

**`setTheme(theme)`** (new helper)
- Applies `data-theme` attribute and updates `aria-label` on the toggle button.
- Does **not** write to `localStorage` — used for silent application at startup.

**`initTheme()` — rewritten**
- Resolves the starting theme in priority order:
  1. Explicit preference saved in `localStorage`
  2. OS `prefers-color-scheme` media query (light or dark)
  3. Default: dark
- Wraps the DOM update in a `no-transitions` class guard: added before the call,
  removed after two `requestAnimationFrame` ticks. This ensures the browser commits
  the repaint before transitions are re-enabled, eliminating the dark→light flash on
  first load for light-mode users.

**`applyTheme(theme)`** — now delegates to `setTheme`, then saves to `localStorage`.
Only called on explicit user interaction, so OS-inferred defaults are not locked in.

**`toggleTheme()`** — unchanged logic; calls `applyTheme` so each click persists.

#### `style.css` (`v=12`)

**`.no-transitions` / `.no-transitions *`**
- Sets `transition: none !important` and `animation: none !important` on every
  element while the class is present, preventing any CSS transition from firing during
  the JS-initiated initial paint.

**`@media (prefers-reduced-motion: reduce)`**
- Disables `transition` and `animation` on all theme-animated elements (body,
  sidebar, chat area, message bubbles, input, toggle button, icons) for users who
  have enabled the OS reduced-motion setting (e.g. vestibular disorder support).

### Design decisions
| Decision | Rationale |
|---|---|
| Two `rAF` calls | A single `rAF` fires before the browser has painted; the second guarantees the repaint is committed |
| `setTheme` vs `applyTheme` split | Separates "apply silently" from "apply and persist" — OS detection shouldn't lock the user into a preference |
| `prefers-color-scheme` as secondary default | Avoids jarring dark-mode flash for users whose OS is already in light mode |
| `prefers-reduced-motion` via CSS media query | Keeps JS free of motion logic; CSS is the canonical place for animation control |

---

## Implementation Details — All Elements Verified for Both Themes

### Feature summary
Full audit of every existing element against both themes. Fixed orphaned CSS variables,
hardcoded colours, and incomplete transition coverage to ensure a consistent, smooth
crossfade for every visible part of the UI.

### Files changed

#### `style.css` (`v=13`)

**Welcome message — orphaned variables wired up**

`--welcome-bg` and `--welcome-border` were defined in both `:root` and
`[data-theme="light"]` but the rule that styles `.message.welcome-message
.message-content` was using `var(--surface)` and `var(--border-color)` instead.
The rule has been corrected to use the dedicated welcome variables:

| Theme | `--welcome-bg` | `--welcome-border` |
|---|---|---|
| Dark | `#1e3a5f` (dark blue tint) | `#2563eb` (blue) |
| Light | `#dbeafe` (blue-100 tint) | `#2563eb` (blue) |

This restores the intended design: the welcome message now has a distinctive
blue-tinted background that sets it apart from ordinary assistant messages in
both themes, maintaining visual hierarchy.

**`--welcome-shadow` variable added**

The welcome message box-shadow was hardcoded as `rgba(0, 0, 0, 0.2)` — a dark shadow
that sits awkwardly on the `#dbeafe` light-mode background. Replaced with a variable:

| Theme | `--welcome-shadow` |
|---|---|
| Dark | `0 4px 16px rgba(0, 0, 0, 0.25)` (dark drop shadow) |
| Light | `0 4px 16px rgba(37, 99, 235, 0.1)` (soft blue glow) |

**Transition list expanded**

Six elements were missing from the theme crossfade transition selector, causing them
to snap between colour values rather than fade smoothly:

| Element | Property affected |
|---|---|
| `.sources-collapsible` | `color` (summary text) |
| `.course-title-item` | `border-bottom-color` |
| `.stat-label` | `color` |
| `.stat-value` | `color` |
| `.course-titles-header` | `color` |
| `.message-meta` | `color` |

All six added to both the main transition selector block and the
`@media (prefers-reduced-motion: reduce)` opt-out block.

### Full element audit

| Element | Dark ✓ | Light ✓ | Notes |
|---|---|---|---|
| `body` | ✓ | ✓ | `--background` / `--text-primary` |
| `.sidebar` | ✓ | ✓ | `--surface` (white in light) |
| `.chat-main` / `.chat-container` | ✓ | ✓ | `--background` |
| `.message.user .message-content` | ✓ | ✓ | `--user-message` (blue); white text fine both themes |
| `.message.assistant .message-content` | ✓ | ✓ | `--surface` |
| `.message.welcome-message .message-content` | ✓ | ✓ | `--welcome-bg` + `--welcome-border` (now used) |
| `.sources-content a` | ✓ | ✓ | `--source-link-*` variables |
| `.sources-content span` | ✓ | ✓ | `--source-span-color` |
| `.message-content code / pre` | ✓ | ✓ | `--code-bg` |
| `.message-content blockquote` | ✓ | ✓ | `--primary-color` (bug fixed) |
| `.error-message` / `.success-message` | ✓ | ✓ | `--error-*` / `--success-*` |
| `#chatInput` | ✓ | ✓ | `--surface` / `--text-primary` |
| `#sendButton` | ✓ | ✓ | `--primary-color` (same both themes) |
| `.new-chat-btn` | ✓ | ✓ | `--text-secondary` + hover `--primary-color` |
| `.stats-header` / `.suggested-header` | ✓ | ✓ | `--text-secondary` |
| `.stat-item` | ✓ | ✓ | `--background` + `--border-color` |
| `.stat-label` / `.stat-value` | ✓ | ✓ | `--text-secondary` / `--primary-color` |
| `.course-title-item` | ✓ | ✓ | `--text-primary` + `--border-color` |
| `.suggested-item` | ✓ | ✓ | `--background` + hover `--surface-hover` |
| `.theme-toggle` | ✓ | ✓ | `--toggle-*` variables |
| Scrollbars | ✓ | ✓ | `--surface` + `--border-color` |
