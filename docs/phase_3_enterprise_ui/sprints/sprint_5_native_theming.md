# Sprint 5: Native Theming & Anti-Chrome Architecture

**Goal:** Hijack Streamlit's global styling engine. Eradicate all native visual artifacts that signal "internal tool" and replace them with a foundational dark-mode Enterprise theme.

## 🎯 Deliverables

1. **Semantic Design Tokens:** 
   - Create `.streamlit/config.toml`.
   - Define `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, and `textColor` per the Phase 3 Spec.

2. **Native CSS Asset Management:**
   - Create `src/bdis/frameworks/ui/assets/style.css` to enforce the Single Responsibility Principle.
   - Inject the stylesheet dynamically into the `app.py` document head.

3. **Anti-Chrome Mechanics:**
   - Define CSS targets for `#MainMenu`, `footer`, and `.stApp header`.
   - Set elements to `display: none;` or `transparent`.

## ✅ Definition of Done
- The default top-right hamburger menu and Streamlit footer are completely invisible.
- The UI background color responds strictly to the TOML configuration.
- Zero CSS syntax strings exist inside `.py` wrapper files.
