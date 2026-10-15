# internship

## QualiTrack — Factory Quality & Dispatch Management

A modern, industrial-grade quality assurance, metrological inspection, and factory dispatch clearance management system built with Python, Django, SQLite, Bootstrap 5, and ReportLab.

### Overview
QualiTrack is an internship project developed by **Animesh Mishra** for **Zapuza Technologies LLP**. It streamlines factory operations across inspection logging, supervisor reviews, dispatch gate clearance, and official Certificate of Analysis (COA) generation.

---

### Core Features

1. **Role-Based Authentication & Navigation (Feature 1)**
   - Role-validated login supporting **Inspectors**, **Supervisors**, and **System Administrators**.
   - Strict role mismatch detection and backend route protection (`@role_required`).

2. **Precision Metrology Inspections (Feature 2)**
   - Auto-calculated conformance (`PASS` / `FAIL`) against Lower Specification Limit (LSL) and Upper Specification Limit (USL).
   - Dynamic JavaScript unit conversion engine (mm, cm, in, µm).
   - Mandatory 2-photo defect documentation for out-of-tolerance measurements.

3. **Supervisor Review & Anti-Self-Approval Protection (Feature 3)**
   - Supervisor review actions: `Approve`, `Reject`, `Return for Rework` with required audit remarks.
   - Database-enforced anti-self-approval rule: inspectors cannot approve their own inspection records.

4. **Dispatch Clearance & Process Holds (Feature 4)**
   - Multi-rule clearance validation before releasing batches for dispatch.
   - Comprehensive Process Hold system with active blocking reasons and audited releases.

5. **Official Certificate of Quality & Dispatch Release (COA)**
   - Vector-sharp, industrial A4 PDF generation via ReportLab.
   - Print-optimized single-sheet layout (`@media print`) with zero orphan page breaks.
   - Tamper-evident cryptographic **SHA-256 digest** recorded for metrology traceability.

---

### Tech Stack
- **Backend:** Python 3.13, Django 6.1
- **Database:** SQLite
- **Frontend:** HTML5, Vanilla CSS, Bootstrap 5, Bootstrap Icons, Chart.js
- **PDF Generation:** ReportLab 4.4
- **Testing:** Comprehensive Django test suite (28/28 tests passing)
