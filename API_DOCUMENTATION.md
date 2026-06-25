# Online Job Portal System - REST API Documentation

This document describes all REST API endpoints implemented in the application.

## Base URL
`/api`

---

## 1. Authentication & Sessions (Form & Session Routes)
These endpoints are handled under the root router path (`/`) using browser form submissions.

### Login Session
* **Method**: `POST`
* **URL**: `/login`
* **Authentication**: None
* **Payload**: Form data with `email` and `password`.
* **Description**: Verifies credentials, starts a browser session, and redirects to `/dashboard`.

### Signup Registration
* **Method**: `POST`
* **URL**: `/signup`
* **Authentication**: None
* **Payload**: Form data with `role`, `fullName`, `email`, `password`, `confirmPassword`.
* **Description**: Initiates user registration and generates a verification OTP code.

### Verify Registration OTP
* **Method**: `POST`
* **URL**: `/verify-otp`
* **Authentication**: None
* **Payload**: Form data with `otp`.
* **Description**: Validates the signup code and registers the user in the database.

---

## 2. Job Discovery & Management REST APIs
All routes below use JSON parameters or multipart files.

### Fetch & Search Jobs List
* **Method**: `GET`
* **URL**: `/api/jobs`
* **Authentication**: None
* **Query Parameters**:
  - `keyword` (Optional): Searches in title, company, description, and skills.
  - `title` (Optional): Filters by job title.
  - `company` (Optional): Filters by company name.
  - `location` (Optional): Filters by geographic location.
  - `skills` (Optional): Matches matching skills.
  - `salary` (Optional): Matches salary fields.
  - `experience` (Optional): Filters by experience level.
  - `job_type` (Optional): Filters by type (e.g., Full Time, Internship).
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "title": "Senior Flask Engineer",
      "company": "Stripe",
      "location": "Remote",
      "salary": "$135,000 - $160,000",
      "job_type": "Full Time",
      "experience": "3+ Years Exp",
      "skills": "Python, Flask, PostgreSQL",
      "description": "Job details...",
      "date_posted": "25 Jun 2026",
      "recruiter_id": 2
    }
  ]
  ```

### Get Single Job Detail
* **Method**: `GET`
* **URL**: `/api/jobs/<int:job_id>`
* **Authentication**: None
* **Success Response (200 OK)**:
  ```json
  {
    "id": 1,
    "title": "Senior Flask Engineer",
    "company": "Stripe",
    ...
  }
  ```

### Post a New Job
* **Method**: `POST`
* **URL**: `/api/jobs`
* **Authentication**: Required (Role: `recruiter`)
* **Payload (JSON/Form)**:
  ```json
  {
    "title": "Frontend Architect",
    "company": "Google",
    "location": "San Francisco, CA",
    "salary": "$180,000 - $220,000",
    "job_type": "Full Time",
    "experience": "Senior",
    "skills": "React, TypeScript, CSS3",
    "description": "Responsibilities and details..."
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "message": "Job posted successfully!",
    "job_id": 2
  }
  ```

### Edit Job Details
* **Method**: `PUT`
* **URL**: `/api/jobs/<int:job_id>`
* **Authentication**: Required (Role: `recruiter`, owner of the listing)
* **Payload (JSON/Form)**:
  ```json
  {
    "title": "Frontend Architect (Updated)",
    "company": "Google",
    "location": "Remote / San Francisco",
    "salary": "$200,000 - $240,000",
    "job_type": "Full Time",
    "experience": "Senior / Lead",
    "skills": "React, TypeScript, CSS",
    "description": "Updated job details..."
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Job updated successfully!",
    "job_id": 2
  }
  ```

### Delete Job Posting
* **Method**: `DELETE`
* **URL**: `/api/jobs/<int:job_id>`
* **Authentication**: Required (Role: `recruiter`, owner of the listing)
* **Description**: Removes the job posting. Cascades deletion to remove all associated applicant records.
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Job deleted successfully!",
    "job_id": 2
  }
  ```

---

## 3. Application Submission & Pipelines

### Submit Job Application
* **Method**: `POST`
* **URL**: `/api/jobs/<int:job_id>/apply`
* **Authentication**: Required (Role: `seeker`)
* **Payload (Multipart Form Data)**:
  - `cover_letter` (Text): Cover letter.
  - `resume_link` (Text URL): Cloud link to portfolio/resume.
  - `resume_file` (Binary File upload, Optional): Local PDF/DOC file.
* **Description**: Submits applicant details. Prevents duplicate applications automatically.
* **Success Response (201 Created)**:
  ```json
  {
    "message": "Application submitted successfully!",
    "application_id": 5
  }
  ```

### Get Application Records
* **Method**: `GET`
* **URL**: `/api/applications`
* **Authentication**: Required (Seeker or Recruiter)
* **Description**:
  - For **Seekers**: Returns personal application history.
  - For **Recruiters**: Returns candidate applications matching their job postings.
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": 5,
      "job_id": 1,
      "job_title": "Senior Flask Engineer",
      "company": "Stripe",
      "seeker_name": "Om Shukla",
      "seeker_email": "seeker@example.com",
      "status": "Pending",
      "date_applied": "25 Jun 2026",
      "resume_link": "https://drive.google.com/...",
      "resume_filename": "resume.pdf",
      "cover_letter": "Short cover message..."
    }
  ]
  ```

### Secure Resume Downloader
* **Method**: `GET`
* **URL**: `/api/applications/<int:app_id>/download`
* **Authentication**: Required (Must be the seeker who submitted the file, or the recruiter who owns the job posting)
* **Description**: Downloads the binary resume file securely.
* **Success Response (200 OK)**: File Stream (Attachment).

### Update Application Status
* **Method**: `PUT`
* **URL**: `/api/applications/<int:app_id>`
* **Authentication**: Required (Role: `recruiter`, owner of the listing)
* **Payload (JSON/Form)**:
  ```json
  {
    "status": "Interviewing"
  }
  ```
  *(Allowed Statuses: `Pending`, `Reviewed`, `Interviewing`, `Offered`, `Rejected`)*
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Application status updated to \"Interviewing\" successfully!",
    "application_id": 5,
    "status": "Interviewing"
  }
  ```

---

## 4. Profile Management APIs

### Update Profile Metadata
* **Method**: `POST`
* **URL**: `/api/profile`
* **Authentication**: Required
* **Payload (JSON/Form)**:
  ```json
  {
    "bio": "Updated professional bio...",
    "skills": "Python, Flask, JavaScript",
    "experience": "Previous roles...",
    "education": "Certifications..."
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Profile details updated successfully!",
    "profile": {
      "bio": "...",
      "skills": "..."
    }
  }
  ```

### Upload Profile Avatar Picture
* **Method**: `POST`
* **URL**: `/api/profile/upload-picture`
* **Authentication**: Required
* **Payload (Multipart File upload)**:
  - `profile_pic` (Image file): PNG, JPG, JPEG, GIF formats.
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Profile picture updated successfully!",
    "filename": "avatar_1_162464000_photo.png"
  }
  ```

### Upload Default Seeker Resume
* **Method**: `POST`
* **URL**: `/api/profile/upload-resume`
* **Authentication**: Required (Role: `seeker`)
* **Payload (Multipart File upload)**:
  - `resume_file` (Document file): PDF, DOC, DOCX formats.
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Default resume uploaded successfully!",
    "filename": "resume.pdf"
  }
  ```

### Change Password
* **Method**: `POST`
* **URL**: `/api/profile/change-password`
* **Authentication**: Required
* **Payload (JSON/Form)**:
  ```json
  {
    "current_password": "old_password",
    "new_password": "new_password",
    "confirm_password": "new_password"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "message": "Password changed successfully!"
  }
  ```

### Serve Public Static Avatars
* **Method**: `GET`
* **URL**: `/api/uploads/<filename>`
* **Authentication**: None
* **Description**: Serves public static files (such as profile picture thumbnails). Employs file name checks to secure against path traversal attacks.
* **Success Response (200 OK)**: Image File Stream.
