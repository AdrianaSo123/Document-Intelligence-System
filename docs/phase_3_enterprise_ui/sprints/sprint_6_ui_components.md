# Sprint 6: Component Architecture & Glassmorphism

**Goal:** Rebuild the flat, linear layout into an Edge-to-Edge interactive Dashboard. Push complex data representation into strictly Humble View components.

## 🎯 Deliverables

1. **Structural Layout Restructuring (`app.py`):** 
   - Implement the "Command Rail" using `st.sidebar` to hold the Uploader module.
   - Dedicate the Main Stage completely to KPI metrics and the data grid.

2. **The Tabular Engine Upgrade (`components/data_table.py`):**
   - Override basic pandas dataframe injection.
   - Implement `st.column_config.NumberColumn` for USD formatting.
   - Implement `st.column_config.CheckboxColumn` mapped strictly to `DashboardViewModel.is_high_risk`.

3. **Glassmorphism CSS Injection:**
   - Define custom CSS variables in `style.css`.
   - Wrap Metric cards with translucent `rgba` borders and implement Y-axis `hover` micro-animations.
   - Apply `backdrop-filter: blur(10px)` to the native dataframe container classes.

## ✅ Definition of Done
- The uploader widget is successfully docked in the left sidebar.
- USD values render with standard dollar-sign string formatting.
- `data_table.py` performs absolutely zero mathematical calculations to determine risk (Humble Object adherence).
