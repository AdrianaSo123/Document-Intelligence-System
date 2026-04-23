# Phase 3: Enterprise Design System (Fortune 500 UX Parity)

## 1. Executive Summary
The goal of Phase 3 is to permanently break away from Streamlit's default "internal tool" aesthetic. By overriding native components with intense CSS injections and establishing a unified semantic design system, the Business Document Intelligence System (BDIS) will be graphically elevated to the standards of tier-1 enterprise SaaS platforms (e.g., Datadog, Palantir Foundry).

## 2. Semantic Design Tokens (`.streamlit/config.toml`)
Streamlit's global theme engine will be hijacked to enforce extreme visual cohesion.

*   **Primary Corporate Color:** `#00f2fe` (Neon Cyan/Blue - high tech aesthetic)
*   **Base Background:** `#0A0E17` (Deep Void - reduces eye strain for analysts)
*   **Secondary Background (Sidebar/Cards):** `#111827` (Card Elevation - provides depth layering)
*   **Text Hierarchy:** `#E2E8F0` (Slightly dimmed off-white for reading comfort)
*   **Typography:** OS-native Sans Serif (Inter/Roboto) for flawless rendering.

## 3. Structural Layout Architecture (`app.py`)
Streamlit defaults to a top-to-bottom blog-post feed. We will forcibly architect an **Edge-to-Edge Dashboard**.

### 3.1 The Command Rail (Sidebar)
The left sidebar will act as the operations center. It will isolate input mechanics from output reporting:
*   **Branding & Status:** System online indicators.
*   **Ingestion Engine:** The `st.file_uploader` will be securely housed here to maximize main-stage real estate.

### 3.2 The Main Stage (Dashboard)
Reserved exclusively for executive summarization and tabular drill-downs. 
*   **Top Row:** Core KPI Cards (Documents Processed, Revenue Parsed, High-Risk Flags).
*   **Bottom Span:** Full-width, borderless Data Grid.

## 4. Native CSS Asset Management (`assets/style.css`)
To adhere to the Single Responsibility Principle, CSS logic must not be concatenated as raw strings inside `.py` python files. 
*   **[NEW] `src/bdis/frameworks/ui/assets/style.css`**: All layout definitions will be housed here. A utility function will read this file buffer and inject it into the Streamlit header.
*   **Anti-Chrome**: Streamlit's native headers (`#MainMenu`, `footer`, `.stApp header`) will be set to `display: none` or `transparent`.

## 5. CSS Variable Injection (Glassmorphism)
Hardcoded hex colors inside CSS are banned to prevent branding drift. The CSS will depend dynamically on CSS Custom Properties declared in the `:root`.

*   **Metric Cards:** Wrapped in var-driven borders (`border: 1px solid var(--border-subtle)`). Y-axis dropshadow hover states are enforced cleanly inside the `<style>` sheet.
*   **Data Grid:** Leverages native `backdrop-filter: blur(10px)` integrated flawlessly via native `.stDataFrame` CSS class targets.

## 6. The Humble Object Boundary (Data Grids)
The View (Streamlit components) must be **mathematically stupid**. It cannot derive business logic. 
*   **The Bound Model:** The UI must ingest the `DashboardViewModel` explicitly. 
*   **Risk Determination:** If a row needs to glow red for "High Risk," the View must simply check `if view_model.is_high_risk:`. It must **never** check `if int(amount) > 10000:` (Domain Leakage).
*   **The Tabular Engine:** `st.column_config` will execute the passive visual mapping of the data (rendering checkboxes, formatting native USD string `$%.2f`).

## 7. State Management & Caching Strictures
Streamlit operates on a reactive, top-down execution loop. Without strict architectural barriers, every UI interaction will accidentally DDoS the backend.
*   **The Network Memoization Rule:** Any component calling `BdisApiClient.fetch_all_documents` must be wrapped in `@st.cache_data(ttl=15)`. This creates a 15-second local TTL bucket that physically bars the Streamlit UI loop from overwhelming the API.

## 8. Graceful Degradation (Error Boundaries)
A Fortune 500 application *never* bleeds a raw Python stack trace to an executive. 
*   **The Void State:** If Celery or FastAPI crashes, `BdisApiClient` will return an `ErrorViewModel`.
*   **Asset Injection:** `app.py` must intercept this Error ViewModel and route the View exclusively to `render_error_state()`, displaying a polished, semantic warning card rather than defaulting to Streamlit's native red crash logs.
