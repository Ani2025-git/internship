# QualiTrack — Factory Quality & Dispatch Management System

A web-based quality inspection and dispatch management application developed as part of the Python Django Developer Internship assignment for **Zapuza Technologies LLP**.

---

## Project Information

| Property | Details |
| :--- | :--- |
| **Project Name** | QualiTrack |
| **Developer** | Animesh Mishra |
| **Project Type** | Web Application |
| **Framework** | Django 5.1+ / 6.1 |
| **Language** | Python 3.13 |
| **Database** | SQLite (Production compatible with PostgreSQL via `dj-database-url`) |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Icons** | Bootstrap Icons |
| **Charts** | Chart.js |
| **PDF Generation** | ReportLab 4.x |

---

## Project Links

- **Live Demo:** [https://internship-n3dc.onrender.com/](https://internship-n3dc.onrender.com/)
- **GitHub Repository:** [https://github.com/Ani2025-git/internship](https://github.com/Ani2025-git/internship)
- **Demo Video:** [https://drive.google.com/file/d/1sGgogNy0hQulfTqBFnkYphnFr93O358a/view?usp=sharing](https://drive.google.com/file/d/1sGgogNy0hQulfTqBFnkYphnFr93O358a/view?usp=sharing)

> **Note:** The demonstration video is hosted on Google Drive with public view access and includes the project overview, code explanation, and a walkthrough of the working features.

---

## 1. Project Overview

**QualiTrack** is designed to support quality inspection and dispatch workflows in a manufacturing environment.

The application helps users record product measurements, evaluate inspection results against specification limits, review inspection records, manage quality-related holds, and check whether the required conditions for dispatch have been satisfied.

It aims to improve inspection traceability, support consistent quality checks, and reduce the risk of dispatching products before the required quality procedures are completed.

---

## 2. Problem Statement

Manufacturing quality workflows require accurate measurements, clear inspection records, supervisor reviews, and reliable dispatch checks.

When these activities are handled inconsistently, teams may face problems such as:
- Incorrect or incomplete inspection records.
- Difficulty identifying out-of-specification measurements.
- Missing defect evidence.
- Insufficient review and approval tracking.
- Dispatch attempts before required quality checks are complete.
- Difficulty preparing quality documentation.

QualiTrack aims to organize these activities in a centralized web application.

---

## 3. Objectives

The main objectives of the project are to:
- Record and manage product inspection data.
- Evaluate measurements against lower and upper specification limits.
- Support different user roles and responsibilities.
- Require defect evidence for applicable failed inspections.
- Support supervisor review and rework workflows.
- Track quality holds and dispatch clearance conditions.
- Generate a Certificate of Analysis (COA) PDF from available inspection information.
- Improve the traceability of quality-related activities.

---

## 4. Key Features

### 4.1 Role-Based Access
The application is designed for the following roles:
- **Inspector:** Records inspections and views relevant inspection information.
- **Supervisor:** Reviews submitted inspections and performs permitted review actions.
- **System Administrator:** Manages administrative functions available to the configured administrator role.

Access to each function strictly follows server-enforced permissions (`@role_required` decorator and model-level validation).

### 4.2 Inspection Management
The inspection workflow allows users to record product inspection information and the relevant measurement values. Inspection records help organize quality checks and provide a history of recorded inspection activity.

### 4.3 Automatic PASS/FAIL Evaluation
Measurements are evaluated against the configured specification limits:
- **PASS:** The measurement is within the permitted specification range (`LSL <= Measurement <= USL`).
- **FAIL:** The measurement is outside the permitted specification range.

The evaluation uses the actual lower specification limit (LSL) and upper specification limit (USL) configured for the inspected parameter.

### 4.4 Measurement Unit Conversion
The application supports measurement unit conversion for the configured units:
- Millimetres (`mm`)
- Centimetres (`cm`)
- Inches (`in`)
- Micrometres (`µm`)

Converted values are handled consistently with the measurement and specification logic.

### 4.5 Defect Evidence
For applicable out-of-tolerance results, the application requires **two defect photos** before submission can proceed. This supports thorough documentation of inspection failures and provides visual evidence for subsequent review.

### 4.6 Supervisor Review Workflow
The supervisor review workflow supports the following actions, subject to the application's implemented rules:
- **Approve** an inspection.
- **Reject** an inspection.
- **Return for Rework** an inspection.

Review remarks and approval restrictions improve accountability and prevent self-approval (an inspector cannot approve their own inspection record).

### 4.7 Quality Hold Management
The application supports operational quality holds. A hold indicates that the relevant item or process requires further action before the applicable workflow can proceed. Holds must be explicitly released with documented supervisor remarks.

### 4.8 Dispatch Clearance
Dispatch clearance checks whether the required inspection and approval conditions have been satisfied. Where required conditions remain incomplete or an applicable hold is active, dispatch remains blocked according to the implemented business rules.

### 4.9 Certificate of Analysis (COA)
The application supports generating a Certificate of Analysis as a PDF using ReportLab. The certificate is formatted as an A4 single-sheet document presenting inspection results, supervisor sign-offs, and dispatch release status.
- **Cryptographic Traceability:** Includes a SHA-256 digest calculated from inspection records and certificate data to support metrology traceability and verify record integrity.

### 4.10 Dashboard and Reporting
The application provides role-oriented dashboard information and inspection-related summaries. Chart.js is integrated for data visualization, displaying pass/fail rates and inspection trends.

---

## 5. Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python 3.13** | Application programming language |
| **Django 5.1+ / 6.1** | Backend web framework |
| **SQLite** | Relational database (default development environment) |
| **HTML5** | Page structure |
| **CSS3** | Styling and responsive layouts |
| **Bootstrap 5** | Responsive user interface framework |
| **JavaScript** | Client-side interactions and dynamic forms |
| **Bootstrap Icons** | Interface icons |
| **Chart.js** | Charts and data visualization |
| **ReportLab 4.x** | PDF Certificate of Analysis (COA) generation |
| **Gunicorn & WhiteNoise** | WSGI HTTP Server and static file serving for production |
| **Git and GitHub** | Version control and source-code hosting |

---

## 6. Application Workflow

The intended high-level workflow is:
1. **Sign In:** An authorized user signs in with role verification.
2. **Record Inspection:** The Inspector selects a production batch and records product measurements.
3. **Automated Conformance Check:** The system evaluates the measurement against the configured specification limits (LSL and USL).
4. **Defect Documentation:** If an applicable measurement fails, mandatory defect evidence (minimum 2 defect photos) must be uploaded.
5. **Supervisor Review:** The inspection proceeds through the supervisor review workflow (Approve, Reject, or Return for Rework) with mandatory audit remarks. Anti-self-approval prevents inspectors from approving their own work.
6. **Process Holds:** Operational holds block progress until explicitly resolved and released by an authorized supervisor.
7. **Dispatch Clearance Check:** The system verifies all clearance conditions:
   - All required inspections are completed and approved.
   - No active quality holds exist.
8. **COA Generation:** A verified Certificate of Analysis PDF is generated with an authentic SHA-256 integrity digest.

---

## 7. Project Structure

The actual project structure of the repository is as follows:

```text
internship/
├── manage.py                     # Django management script
├── requirements.txt              # Project Python dependencies
├── README.md                     # Project documentation and guide
├── Procfile                      # Render / Heroku process configuration
├── render.yaml                   # Infrastructure-as-code deployment blueprint
├── build.sh                      # Production build script (migrate, collectstatic)
├── db.sqlite3                    # Local SQLite database
│
├── factory_system/               # Django project configuration folder (config)
│   ├── __init__.py
│   ├── asgi.py                   # ASGI configuration
│   ├── settings.py               # Django configuration, database & security settings
│   ├── urls.py                   # Root URL routing
│   └── wsgi.py                   # WSGI entry point for web deployment
│
├── operations/                   # Core application folder (your_app)
│   ├── __init__.py
│   ├── admin.py                  # Django administrative interface configuration
│   ├── apps.py                   # App configuration
│   ├── decorators.py             # Role-based access control decorators (@role_required)
│   ├── forms.py                  # Inspection, review, and hold submission forms
│   ├── models.py                 # Data models: Job, Inspection, Hold, DefectPhoto, COA
│   ├── pdf_generator.py          # ReportLab PDF Certificate of Analysis generation
│   ├── tests.py                  # Automated test suite (33 comprehensive tests)
│   ├── urls.py                   # Application routing endpoints
│   ├── views.py                  # View controllers & business logic
│   │
│   ├── management/               # Custom management commands
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── seed_data.py      # Seed command for initial demo data and accounts
│   │
│   └── migrations/               # Database schema migrations
│       ├── 0001_initial.py
│       └── __init__.py
│
├── templates/                    # HTML5 presentation templates
│   ├── base.html                 # Master layout template
│   ├── home.html                 # Landing page
│   ├── auth/                     # Authentication & login templates
│   ├── dashboards/               # Role-specific dashboards (Inspector, Supervisor, Admin)
│   ├── holds/                    # Quality hold management templates
│   ├── inspections/              # Inspection forms and detail views
│   ├── jobs/                     # Production job lists and creation
│   └── reviews/                  # Supervisor review templates
│
├── static/                       # Static assets
│   └── css/                      # Custom stylesheets
│
├── staticfiles/                  # Collected static files for production
└── media/                        # User-uploaded files (defect photos & evidence)
```

---

## 8. Installation and Setup

### Prerequisites
- **Python 3.13** (or Python 3.10+)
- **pip** (Python package manager)
- **Git**
- A terminal or command prompt

### Step 1: Clone the Repository
```bash
git clone https://github.com/Ani2025-git/internship.git
cd internship
```

### Step 2: Create a Virtual Environment
- **On Windows:**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **On macOS or Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure the Environment
Review the Django settings in `factory_system/settings.py`. Configure environment variables as needed for local or production use (e.g. `SECRET_KEY`, `DEBUG`, `DATABASE_URL`).

### Step 5: Apply Database Migrations
```bash
python manage.py migrate
```

### Step 6: Seed Demo Data (Optional)
To pre-populate sample jobs, inspections, process holds, defect photos, and test accounts:
```bash
python manage.py seed_data
```
*Default seeded test accounts: `admin` (System Admin), `inspector1` (Inspector), `supervisor1` (Supervisor) — password: `password123`.*

Alternatively, create an administrator account manually:
```bash
python manage.py createsuperuser
```

### Step 7: Start the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to:
- **Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 9. Testing and Validation

The application includes a comprehensive test suite in `operations/tests.py` covering all core functionalities:
- **Authentication & RBAC:** Role selection validation, role mismatch detection, and route protection.
- **Anti-Self-Approval:** Prevention of inspectors approving their own submitted inspections.
- **Tolerance Calculation:** Automatic calculation of PASS/FAIL against lower (LSL) and upper (USL) limits.
- **Unit Conversion:** Validation of measurements across mm, cm, in, and µm.
- **Mandatory Defect Evidence:** Enforcement of 2 uploaded defect photos for out-of-tolerance results.
- **Supervisor Workflow:** Approve, Reject, and Return for Rework actions with mandatory audit remarks.
- **Process Holds:** Hold creation, blocking effects, and hold release workflows.
- **Dispatch Clearance:** Multi-rule validation blocking dispatch when inspections are incomplete or holds are active.
- **COA Generation & SHA-256 Digest:** PDF generation via ReportLab and cryptographic digest calculation.

### Run Automated Tests
```bash
python manage.py test
```

### Actual Test Results
```text
Creating test database for alias 'default'...
.................................
----------------------------------------------------------------------
Ran 33 tests in 87.784s

OK
Destroying test database for alias 'default'...
Found 33 test(s).
System check identified no issues (0 silenced).
```
**Test Status:** **33/33 tests passing (100% pass rate).**

---

## 10. Security Considerations

Security and data integrity are fundamental to QualiTrack:
- **Server-Side Authorization:** Enforced via the `@role_required` decorator and backend models, ensuring permissions are not bypassed via client-side manipulation.
- **Anti-Self-Approval Integrity:** Database-level and view-level rules prevent inspectors from approving or rejecting their own inspection submissions.
- **CSRF Protection:** All state-changing POST requests require Django's CSRF tokens.
- **Credential & Secret Protection:** Sensitive configurations, secret keys, and credentials use environment variable overrides for production deployment.
- **Upload Validation:** Uploaded defect photos are validated for valid image formats (JPEG, PNG) and file size limits.
- **Cryptographic Traceability:** Expected SHA-256 digests are calculated from inspection data and stored for COA certificate verification.
- **Production Hardening:** Configured for HTTPS, WhiteNoise static compression, and PostgreSQL support via `dj-database-url`.

---

## 11. Limitations and Future Improvements

Potential improvements for future versions:
- Integration with direct digital caliper and IoT metrology hardware (Bluetooth/USB).
- Barcode and QR code scanning for batch tracking on mobile devices.
- Multi-language localization for factory floor personnel.
- Asynchronous task processing (Celery/Redis) for high-volume automated batch inspections.
- Dedicated S3-compatible cloud object storage for defect photo archives.

---

## 12. Live Demo and Video Walkthrough

- **Live Application:** [https://internship-n3dc.onrender.com/](https://internship-n3dc.onrender.com/)
- **Video Walkthrough:** [https://drive.google.com/file/d/1sGgogNy0hQulfTqBFnkYphnFr93O358a/view?usp=sharing](https://drive.google.com/file/d/1sGgogNy0hQulfTqBFnkYphnFr93O358a/view?usp=sharing)

The video recording demonstrates the live application features, walks through the source code structure, and shows the core inspection, supervisor review, and dispatch clearance workflows.

---

## 13. Author

**Animesh Mishra**  
Python Django Developer Internship Candidate  
- **GitHub:** [https://github.com/Ani2025-git](https://github.com/Ani2025-git)
- **Repository:** [https://github.com/Ani2025-git/internship](https://github.com/Ani2025-git/internship)

---

## 14. Acknowledgement

This project was developed as part of the **Python Django Developer Internship assignment** associated with **Zapuza Technologies LLP**.

The project provided an invaluable opportunity to design and implement a practical, industry-grade quality assurance and dispatch management application using Django.

Thank you for reviewing QualiTrack!
