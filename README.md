# Online Job Portal System

A modern, full-stack web application designed for job seekers and corporate recruiters. Built using **Python**, **Flask**, **SQLAlchemy ORM**, and **Bootstrap 5**, the platform features secure role-based authentication, real-time application status pipelines, interactive filter searches, default resume file management, and email OTP validation.

---

## Key Features

1. **User Authentication & Verification**:
   - Secure account creation and session logins using PBKDF2 password hashing via `Werkzeug`.
   - Automated 6-digit email OTP verification codes for new registrations and forgot password recovery.

2. **Role-Based Access Control (RBAC)**:
   - Dedicated dashboard panels customized dynamically for **Job Seekers** and **Recruiters**.
   - Restricted routes (e.g. Recruiters post and edit vacancies; Seekers upload application details).

3. **Job Management Pipeline**:
   - Recruiters can post, edit details, and permanently delete job postings.
   - Deleting a listing cascades automatically to drop all candidate applications, preventing orphan entries.
   - Job listings can be toggled between "All Postings" and "My Postings" on the dashboard.

4. **Applicant Management**:
   - Supports local resume document uploading (`.pdf`, `.doc`, `.docx`) or cloud portfolio URL submissions.
   - Prevents duplicate applications to the same vacancy.
   - Seekers can inspect real-time application stages (Pending, Reviewed, Interviewing, Offered, Rejected) and view their full history.
   - Recruiters can accept or reject candidates via one-click actions.

5. **Profile Customization**:
   - Update professional summary, sector tags, education background, and work experience.
   - Securely upload or update avatar pictures.
   - Change user passwords directly within the profile settings panel.
   - Seekers can upload a default profile resume, which auto-fills application forms.

6. **Interactive Search & Multi-Criteria Filters**:
   - Live debounced keyword search (location, job titles, tags).
   - Multi-criteria filter options for Location, Salary, Experience Requirements, and Job Type (Full Time, Internship, etc.).

7. **REST APIs & AJAX Front-End**:
   - Decoupled REST API backend communicating via JSON payloads.
   - Fluid dynamic interface built on vanilla JS and CSS, allowing seamless navigation without page refreshes.

---

## Tech Stack

* **Core Platform**: Python 3.8+, Flask 3.1.x
* **Database & ORM**: SQLAlchemy 2.x, SQLite (development) / PostgreSQL or MySQL (production)
* **Design & Layout**: Bootstrap 5, Bootstrap Icons, Vanilla CSS
* **Dynamic Frontend**: Vanilla JavaScript (AJAX, DOM elements, FormData, fetch APIs)
* **Mail Dispatcher**: Flask-Mail, SMTP server
* **Configuration**: Python-dotenv (load variables from `.env`)
* **Security & Hashes**: Werkzeug (PBKDF2 passwords, secure file names)

---

## Folder Structure

```text
├── app.py                  # Main entrance. Configures parameters & starts dev server
├── extensions.py           # Instantiates modular extensions (Mail)
├── routes/
│   ├── auth_routes.py      # Flask routes for signup, login, recovery, and sessions
│   ├── api_routes.py       # REST API endpoints for jobs, applications, files, and profiles
│   └── database.py         # SQLAlchemy schemas (auth_users, Job, Application)
├── static/
│   └── style.css           # Premium layout style rules, variables, and animations
├── templates/
│   ├── home.html           # Landing page with CTA actions
│   ├── login.html          # Authentication sign-in form page
│   ├── signup.html         # User registration form page
│   ├── otp_verification.html # Verification OTP code entry page
│   ├── reset_otp.html      # Recovery OTP entry page
│   ├── reset_password.html # Recovery new password set page
│   ├── forgot_password.html # Recovery email trigger page
│   ├── dashboard.html      # Dynamic Seeker and Recruiter dashboard
│   └── post_job.html       # Recruiter's vacancy posting form page
├── uploads/                # Server storage directory for avatar and resume uploads
├── .env                    # Local credentials file (loaded dynamically, git ignored)
├── .env.example            # Sample configuration template
├── .gitignore              # Configures files and paths ignored by git
├── requirements.txt        # Pinned project dependencies
├── API_DOCUMENTATION.md    # Detailed API endpoints list
├── DATABASE_SCHEMA.md      # DB schemas, relations, and index charts
├── LICENSE                 # License terms (MIT)
└── README.md               # User setup & architecture documentation
```

---

## Environment Variables

Copy the configuration template to establish environment configurations:
```bash
cp .env.example .env
```

Configure local credentials inside `.env`:
```ini
# App config
SECRET_KEY=jobportal_secret_key_12345

# Database URL
DATABASE_URL=sqlite:///database.db

# Flask-Mail configurations (SMTP settings)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your_smtp_username@gmail.com
MAIL_PASSWORD=your_smtp_app_password
MAIL_DEFAULT_SENDER=your_smtp_username@gmail.com

# Cookie security settings (True in production under HTTPS)
SESSION_COOKIE_SECURE=False
```

---

## Installation & Setup

### 1. Clone Project
```bash
git clone https://github.com/omshukla/online-job-portal.git
cd online-job-portal
```

### 2. Set Up Virtual Environment
On macOS / Linux:
```bash
python -m venv venv
source venv/bin/activate
```
On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Pinned Dependencies
```bash
pip install -r requirements.txt
```

### 4. Seed Database (Optional)
A seeding script is included to quickly populate test seeker and recruiter accounts:
```bash
python -c "
import sys
sys.path.append('.')
from app import app
from routes.database import db
from werkzeug.security import generate_password_hash
from routes.database import auth_users, Job

with app.app_context():
    # Drop and recreate tables
    db.drop_all()
    db.create_all()
    
    # Seeker (Password: password)
    seeker = auth_users(
        full_name='Om Shukla (Seeker)',
        email='seeker@example.com',
        password=generate_password_hash('password'),
        role='seeker',
        bio='Experienced Software Engineer',
        skills='Python, Flask, JavaScript, SQL'
    )
    db.session.add(seeker)
    
    # Recruiter (Password: password)
    recruiter = auth_users(
        full_name='Renu Shukla (Recruiter)',
        email='recruiter@example.com',
        password=generate_password_hash('password'),
        role='recruiter',
        bio='Tech Recruiter',
        skills='Talent Acquisition'
    )
    db.session.add(recruiter)
    db.session.commit()
    
    # Sample Job
    job = Job(
        title='Full Stack Software Engineer',
        company='Stripe',
        location='Remote, USA',
        salary='\$120k - \$145k',
        job_type='Full Time',
        experience='3+ Years Exp',
        description='We are looking for a Full Stack Software Engineer to build and scale paid pipelines.',
        skills='Flask, Python, SQL, JavaScript',
        date_posted='25 Jun 2026',
        recruiter_id=recruiter.id
    )
    db.session.add(job)
    db.session.commit()
    print('Development databases seeded!')
"
```

### 5. Launch Local Server
```bash
python app.py
```
Open **`http://127.0.0.1:9900`** in your browser. You can immediately log in with:
* **Seeker**: `seeker@example.com` / `password`
* **Recruiter**: `recruiter@example.com` / `password`

---

## Screenshots

Placeholders for interface screenshots:

### Home Landing Page
*Placeholder: `docs/screenshots/home.png`*

### User Login Page
*Placeholder: `docs/screenshots/login.png`*

### User Registration Page
*Placeholder: `docs/screenshots/signup.png`*

### Applicant / Recruiter Dashboard
*Placeholder: `docs/screenshots/dashboard.png`*

### Profile & Resume Settings
*Placeholder: `docs/screenshots/profile.png`*

### Vacancy Posting form
*Placeholder: `docs/screenshots/post_job.png`*

### Candidate Applications console
*Placeholder: `docs/screenshots/applications.png`*

---

## API Summary
For full details, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

* `GET  /api/jobs` - Searches and filters jobs.
* `GET  /api/jobs/<id>` - Fetches detail of a single job.
* `POST /api/jobs` - Posts a new job listing.
* `PUT  /api/jobs/<id>` - Updates an existing job posting.
* `DELETE /api/jobs/<id>` - Deletes a job posting and its applications.
* `POST /api/jobs/<id>/apply` - Seeker submits cover letter and uploads resume.
* `GET  /api/applications` - Returns applications records.
* `GET  /api/applications/<id>/download` - Securely downloads applicant's resume.
* `PUT  /api/applications/<id>` - Recruiter modifies status.
* `POST /api/profile` - Edits user summary details.
* `POST /api/profile/upload-picture` - Uploads profile avatar.
* `POST /api/profile/upload-resume` - Uploads default seeker resume.
* `POST /api/profile/change-password` - Updates profile password safely.

---

## Database Relationships
For ER Diagrams, see [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

* **User (`auth_users`)**: Has a many-to-many relationship with applications, and a one-to-many relationship with job postings.
* **Job (`job`)**: Owned by a Recruiter. Deletion propagates cascade rules to clear associated application entries.
* **Application (`application`)**: Links Job and Candidate. Stores resume files and statuses.

---

## Security Implementations

1. **Password Hashing**: Stored using PBKDF2 hashing via `Werkzeug`.
2. **Access Control (Authorization)**: Manual session evaluations and decorator functions verify role clearances (`seeker` or `recruiter`).
3. **Secure File Uploads**: Validates extensions (`.pdf`, `.docx` for resumes; `.png`, `.jpg` for photos) and forces filenames to secure paths using `secure_filename`.
4. **XSS Protection**: Frontend escapes input fields via `escapeHTML()` before dynamic innerHTML rendering.
5. **SQL Injection**: SQLAlchemy ORM implements parameterized SQL statements automatically.
6. **Session Protections**: Configured `SESSION_COOKIE_HTTPONLY = True` and `SESSION_COOKIE_SAMESITE = 'Lax'` attributes.

---

## Deployment Guide

### 1. Render Setup
1. Fork this repository on GitHub.
2. Log in to Render and create a new **Web Service**. Connect it to your fork.
3. Configure settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app` (You may need to add `gunicorn` to requirements.txt)
4. Add environment variables under **Environment**:
   - `DATABASE_URL` (Postgres URL)
   - `SECRET_KEY` (Random string)
   - `MAIL_USERNAME` / `MAIL_PASSWORD` (SMTP configurations)
   - `SESSION_COOKIE_SECURE` = `True`

### 2. Railway Setup
1. In Railway, click **New Project** -> **Deploy from GitHub repo**.
2. Under Variables, configure `DATABASE_URL` (can bind to a provisioned PostgreSQL service), `SECRET_KEY`, and `MAIL_` credentials.
3. Railway reads the start script or Gunicorn configuration and deploys.

### 3. PythonAnywhere Setup
1. Upload code using Git clone.
2. Set up a virtual environment in the bash console and run `pip install -r requirements.txt`.
3. In the Web Tab, configure the WSGI configuration file:
   ```python
   import sys
   path = '/home/username/online-job-portal'
   if path not in sys.path:
       sys.path.append(path)
   from app import app as application
   ```
4. Define environment variables in PythonAnywhere console or configuration, reload the web app.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Om Shukla**  
Student and Full Stack Developer  
*Email: omshukla2609@gmail.com*
*GitHub: [github.com/omshukla](https://github.com/omshukla)*
