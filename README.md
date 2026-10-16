# QualiTrack — Factory Quality & Dispatch Management

A modern factory quality assurance, metrological inspection, supervisor approval, and dispatch clearance management system built with Python, Django, SQLite, Bootstrap 5, and ReportLab.

---

## Overview
QualiTrack is a factory quality control and dispatch management web application developed by **Animesh Mishra** as an internship project for **Zapuza Technologies LLP**.

The system helps manage dimensional inspections, identify out-of-specification measurements, document defects, review inspections, manage process holds, and control dispatch clearance. It also supports generating an official Certificate of Analysis (COA) PDF for quality and traceability purposes.

---

## Core Features

### 1. Role-Based Authentication & Navigation
- Role-based access for **Inspectors**, **Supervisors**, and **System Administrators**.
- Role mismatch detection during login.
- Protected backend routes using role-based authorization (`@role_required`).
- Role-specific dashboards and navigation.

### 2. Precision Metrology Inspections
- Automatic `PASS` / `FAIL` calculation using Lower Specification Limit (LSL) and Upper Specification Limit (USL).
- Measurement unit conversion support for mm, cm, inches, and µm.
- Defect documentation with mandatory two-photo evidence for out-of-tolerance measurements.
- Inspection records for quality traceability.

### 3. Supervisor Review & Approval
- `Approve`, `Reject`, and `Return for Rework` actions.
- Required audit remarks for supervisor decisions.
- Database-enforced protection against inspectors approving their own inspection records.
- Review status and audit history.

### 4. Dispatch Clearance & Process Holds
- Multi-rule validation before dispatch clearance.
- Process holds with documented blocking reasons.
- Audited hold-release workflow.
- Dispatch restrictions when required checks or approvals are incomplete.

### 5. Certificate of Analysis (COA)
- PDF certificate generation using ReportLab.
- A4 print-oriented single-sheet certificate layout.
- Quality inspection and dispatch release information.
- SHA-256 digest support for record-integrity verification and metrology traceability.
  > **Note:** A SHA-256 digest can help detect changes only when it is calculated and verified against the correct data and the expected digest is stored securely.

---

## Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, Django |
| **Database** | SQLite |
| **Frontend** | HTML5, CSS3, Bootstrap 5 |
| **Icons** | Bootstrap Icons |
| **Charts** | Chart.js |
| **PDF Generation** | ReportLab |
| **Testing** | Django Test Framework |

### Versions Specified for this Project
- **Python:** 3.13
- **Django:** 6.1
- **ReportLab:** 4.4

---

## System Workflow
1. An **Inspector** logs in and selects a production batch.
2. The Inspector records measurements and inspection evidence.
3. The system evaluates measurements against the configured LSL and USL.
4. Out-of-tolerance results require the configured defect-photo evidence (minimum 2 photos).
5. A **Supervisor** reviews the inspection and approves, rejects, or returns it for rework.
6. The system checks required approvals, inspection results, and active process holds.
7. Dispatch clearance is granted only when all applicable clearance rules pass.
8. An authorized user generates the COA PDF when the required conditions are satisfied.

---

## Installation and Setup

### Prerequisites
- Python 3.13
- pip
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Ani2025-git/internship.git
cd internship
```

### 2. Create a Virtual Environment
- **Windows:**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py migrate
```

### 5. Seed Initial Demo Data (Optional)
```bash
python manage.py seed_data
```
> Pre-populates sample production orders, inspections, defect photos, and default accounts (`admin`, `inspector1`, `supervisor1`).

### 6. Create an Administrator Account
```bash
python manage.py createsuperuser
```
Follow the terminal prompts to create the account.

### 7. Start the Development Server
```bash
python manage.py runserver
```
Open the application in your browser:
- **Web Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django Administration:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Running Tests
Run the comprehensive Django test suite:
```bash
python manage.py test
```
The test suite validates authentication, anti-self-approval, tolerance calculation, photo uploads, process holds, dispatch rules, SHA-256 hash generation, and PDF streaming. All **33/33 tests pass**.

---

## Security Considerations
- **Role Permissions:** Enforced on the server via `@role_required` and backend model logic, not only in the user interface.
- **Credential Hygiene:** Passwords, secret keys, production credentials, and sensitive environment variables are kept out of source control.
- **Media & File Protection:** File types and sizes are validated; uploaded media paths are isolated.
- **CSRF Protection:** State-changing requests (POST) are strictly protected using Django's CSRF middleware.
- **Audit Trails:** Complete audit history for inspection reviews, process holds, releases, and dispatch clearances.
- **Cryptographic Traceability:** Expected SHA-256 digests are stored and verified in the database to prevent undetected record tampering.
- **Production Readiness:** Configured with WhiteNoise static handling and `dj-database-url` for cloud deployments (e.g., Render / PostgreSQL).

---

## Project Objectives
- Improve the organization and auditability of factory inspection records.
- Automate dimensional conformance checks against engineering tolerances.
- Support traceable supervisor review and rework decisions.
- Prevent dispatch clearance when mandatory quality checks or active holds remain unresolved.
- Generate structured, print-optimized Certificate of Analysis (COA) documents.

---

## Internship Project
- **Project:** QualiTrack — Factory Quality & Dispatch Management
- **Developer:** Animesh Mishra
- **Organization:** Zapuza Technologies LLP
- **Purpose:** Python Django Developer Internship Project

*QualiTrack is intended to support quality-control workflows. Actual dispatch authorization must follow the organization's approved quality procedures and validated business rules.*
