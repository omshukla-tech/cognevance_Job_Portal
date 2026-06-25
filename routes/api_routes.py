import os
import time
from flask import Blueprint, request, jsonify, session, current_app, send_from_directory, redirect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from routes.database import db, auth_users, Job, Application
from datetime import datetime

# Import Cloudinary libraries dynamically if setup
import cloudinary
import cloudinary.uploader

api = Blueprint('api', __name__)

ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Configure Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name = CLOUDINARY_CLOUD_NAME,
        api_key = CLOUDINARY_API_KEY,
        api_secret = CLOUDINARY_API_SECRET,
        secure = True
    )

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Core upload logic selector: Local in dev vs Cloudinary in prod
def upload_file_to_cloud_or_local(file, folder, is_image=True):
    use_cloudinary = (
        os.getenv('CLOUDINARY_URL') is not None or 
        (os.getenv('CLOUDINARY_CLOUD_NAME') is not None and 
         os.getenv('CLOUDINARY_API_KEY') is not None and 
         os.getenv('CLOUDINARY_API_SECRET') is not None)
    )
    
    if use_cloudinary:
        try:
            if is_image:
                result = cloudinary.uploader.upload(file, folder=folder)
            else:
                result = cloudinary.uploader.upload(file, folder=folder, resource_type="raw")
            # Returns the secure URL hosted on cloud storage
            return result.get('secure_url'), file.filename
        except Exception as e:
            print(f"[CLOUDINARY ERROR] Upload failed: {e}")
            raise e
    else:
        # Development fallback: write to local /tmp/uploads or local uploads folder
        filename = f"{folder}_{int(time.time())}_{secure_filename(file.filename)}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename, file.filename

# Helper to check authentication
def get_current_user():
    if 'user_id' not in session:
        return None
    return auth_users.query.get(session['user_id'])

# 1. GET /api/jobs - Search and Filter jobs
@api.route('/jobs', methods=['GET'])
def get_jobs():
    keyword = request.args.get('keyword', '').strip()
    title = request.args.get('title', '').strip()
    company = request.args.get('company', '').strip()
    location = request.args.get('location', '').strip()
    skills = request.args.get('skills', '').strip()
    salary = request.args.get('salary', '').strip()
    experience = request.args.get('experience', '').strip()
    job_type = request.args.get('job_type', '').strip()

    query = Job.query

    if keyword:
        query = query.filter(
            (Job.title.like(f'%{keyword}%')) |
            (Job.company.like(f'%{keyword}%')) |
            (Job.description.like(f'%{keyword}%')) |
            (Job.skills.like(f'%{keyword}%'))
        )
    if title:
        query = query.filter(Job.title.like(f'%{title}%'))
    if company:
        query = query.filter(Job.company.like(f'%{company}%'))
    if location:
        query = query.filter(Job.location.like(f'%{location}%'))
    if skills:
        query = query.filter(Job.skills.like(f'%{skills}%'))
    if salary:
        query = query.filter(Job.salary.like(f'%{salary}%'))
    if experience:
        query = query.filter(Job.experience.like(f'%{experience}%'))
    if job_type:
        query = query.filter(Job.job_type == job_type)

    jobs = query.order_by(Job.id.desc()).all()
    
    result = []
    for job in jobs:
        result.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'salary': job.salary,
            'job_type': job.job_type,
            'experience': job.experience,
            'skills': job.skills,
            'description': job.description,
            'date_posted': job.date_posted,
            'recruiter_id': job.recruiter_id
        })
    return jsonify(result), 200

# 2. GET /api/jobs/<id> - Get single job details
@api.route('/jobs/<int:job_id>', methods=['GET'])
def get_job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify({
        'id': job.id,
        'title': job.title,
        'company': job.company,
        'location': job.location,
        'salary': job.salary,
        'job_type': job.job_type,
        'experience': job.experience,
        'skills': job.skills,
        'description': job.description,
        'date_posted': job.date_posted,
        'recruiter_id': job.recruiter_id
    }), 200

# 3. POST /api/jobs - Recruiter posts a job
@api.route('/jobs', methods=['POST'])
def create_job():
    user = get_current_user()
    if not user or user.role != 'recruiter':
        return jsonify({'error': 'Unauthorized. Recruiters only.'}), 403

    data = request.get_json() if request.is_json else request.form

    required_fields = ['title', 'company', 'location', 'salary', 'job_type', 'experience', 'skills', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Field "{field}" is required.'}), 400

    new_job = Job(
        title=data.get('title'),
        company=data.get('company'),
        location=data.get('location'),
        salary=data.get('salary'),
        job_type=data.get('job_type'),
        experience=data.get('experience'),
        skills=data.get('skills'),
        description=data.get('description'),
        date_posted=datetime.now().strftime("%d %b %Y"),
        recruiter_id=user.id
    )

    db.session.add(new_job)
    db.session.commit()

    return jsonify({
        'message': 'Job posted successfully!',
        'job_id': new_job.id
    }), 201

# 4. PUT /api/jobs/<id> - Recruiter edits job details
@api.route('/jobs/<int:job_id>', methods=['PUT', 'POST'])
def edit_job(job_id):
    user = get_current_user()
    if not user or user.role != 'recruiter':
        return jsonify({'error': 'Unauthorized. Recruiters only.'}), 403

    job = Job.query.get_or_404(job_id)
    if job.recruiter_id != user.id:
        return jsonify({'error': 'Forbidden. You do not own this job posting.'}), 403

    data = request.get_json() if request.is_json else request.form

    required_fields = ['title', 'company', 'location', 'salary', 'job_type', 'experience', 'skills', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Field "{field}" is required.'}), 400

    job.title = data.get('title')
    job.company = data.get('company')
    job.location = data.get('location')
    job.salary = data.get('salary')
    job.job_type = data.get('job_type')
    job.experience = data.get('experience')
    job.skills = data.get('skills')
    job.description = data.get('description')

    db.session.commit()
    return jsonify({'message': 'Job updated successfully!', 'job_id': job.id}), 200

# 5. DELETE /api/jobs/<id> - Recruiter deletes a job posting
@api.route('/jobs/<int:job_id>', methods=['DELETE', 'POST'])
def delete_job(job_id):
    user = get_current_user()
    if not user or user.role != 'recruiter':
        return jsonify({'error': 'Unauthorized. Recruiters only.'}), 403

    job = Job.query.get_or_404(job_id)
    if job.recruiter_id != user.id:
        return jsonify({'error': 'Forbidden. You do not own this job posting.'}), 403

    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': 'Job deleted successfully!', 'job_id': job_id}), 200

# 6. POST /api/jobs/<id>/apply - Seeker applies to a job (with secure local or cloud upload)
@api.route('/jobs/<int:job_id>/apply', methods=['POST'])
def apply_to_job(job_id):
    user = get_current_user()
    if not user or user.role != 'seeker':
        return jsonify({'error': 'Unauthorized. Job seekers only.'}), 403

    job = Job.query.get_or_404(job_id)

    # Check if user already applied
    existing_app = Application.query.filter_by(job_id=job.id, seeker_id=user.id).first()
    if existing_app:
        return jsonify({'error': 'You have already applied to this job.'}), 400

    cover_letter = request.form.get('cover_letter', '')
    resume_link = request.form.get('resume_link', '')
    
    saved_filename = None
    saved_filepath = None

    # Handle file upload if present
    if 'resume_file' in request.files:
        file = request.files['resume_file']
        if file and file.filename != '':
            if allowed_file(file.filename, ALLOWED_RESUME_EXTENSIONS):
                try:
                    saved_filepath, saved_filename = upload_file_to_cloud_or_local(file, "resumes", is_image=False)
                except Exception as e:
                    return jsonify({'error': f'Resume upload failed: {str(e)}'}), 500
            else:
                return jsonify({'error': 'Invalid file type. Only PDF, DOC, and DOCX are allowed.'}), 400

    # Fallback to defaults
    if not saved_filepath and not resume_link:
        if user.resume_filepath:
            saved_filename = user.resume_filename
            saved_filepath = user.resume_filepath
        else:
            return jsonify({'error': 'Please upload a resume file or enter a resume URL link.'}), 400

    new_app = Application(
        job_id=job.id,
        seeker_id=user.id,
        status='Pending',
        cover_letter=cover_letter,
        resume_link=resume_link,
        resume_filename=saved_filename,
        resume_filepath=saved_filepath,
        date_applied=datetime.now().strftime("%d %b %Y")
    )

    db.session.add(new_app)
    db.session.commit()

    return jsonify({
        'message': 'Application submitted successfully!',
        'application_id': new_app.id
    }), 201

# 7. GET /api/applications - Get applications history list
@api.route('/applications', methods=['GET'])
def get_applications():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401

    result = []
    if user.role == 'seeker':
        apps = Application.query.filter_by(seeker_id=user.id).order_by(Application.id.desc()).all()
        for app in apps:
            result.append({
                'id': app.id,
                'job_id': app.job_id,
                'job_title': app.job.title,
                'company': app.job.company,
                'status': app.status,
                'date_applied': app.date_applied,
                'resume_link': app.resume_link,
                'resume_filename': app.resume_filename,
                'cover_letter': app.cover_letter
            })
    else:
        apps = Application.query.join(Job).filter(Job.recruiter_id == user.id).order_by(Application.id.desc()).all()
        for app in apps:
            result.append({
                'id': app.id,
                'job_id': app.job_id,
                'job_title': app.job.title,
                'company': app.job.company,
                'seeker_name': app.seeker.full_name,
                'seeker_email': app.seeker.email,
                'seeker_id': app.seeker_id,
                'status': app.status,
                'date_applied': app.date_applied,
                'resume_link': app.resume_link,
                'resume_filename': app.resume_filename,
                'cover_letter': app.cover_letter
            })

    return jsonify(result), 200

# 8. GET /api/applications/<id>/download - Secure resume file downloader/redirector
@api.route('/applications/<int:app_id>/download', methods=['GET'])
def download_resume(app_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401

    app_record = Application.query.get_or_404(app_id)
    
    if app_record.seeker_id != user.id and app_record.job.recruiter_id != user.id:
        return jsonify({'error': 'Forbidden. You do not have permissions to access this file.'}), 403

    if not app_record.resume_filepath:
        return jsonify({'error': 'Resume file path is missing.'}), 404

    # If it is a Cloudinary URL link, redirect directly to download
    if app_record.resume_filepath.startswith('http'):
        return redirect(app_record.resume_filepath)
        
    # Local fallback downloads
    if not os.path.exists(app_record.resume_filepath):
        return jsonify({'error': 'File not found on server.'}), 404

    directory = os.path.dirname(app_record.resume_filepath)
    filename = os.path.basename(app_record.resume_filepath)
    return send_from_directory(directory, filename, as_attachment=True, download_name=app_record.resume_filename)

# 9. PUT /api/applications/<id> - Recruiter updates application status
@api.route('/applications/<int:app_id>', methods=['PUT', 'POST'])
def update_application_status(app_id):
    user = get_current_user()
    if not user or user.role != 'recruiter':
        return jsonify({'error': 'Unauthorized. Recruiters only.'}), 403

    app_record = Application.query.get_or_404(app_id)
    if app_record.job.recruiter_id != user.id:
        return jsonify({'error': 'Forbidden. You do not own this job posting.'}), 403

    data = request.get_json() if request.is_json else request.form
    new_status = data.get('status')
    if not new_status or new_status not in ['Pending', 'Reviewed', 'Interviewing', 'Offered', 'Rejected']:
        return jsonify({'error': 'Invalid or missing status.'}), 400

    app_record.status = new_status
    db.session.commit()

    return jsonify({
        'message': f'Application status updated to "{new_status}" successfully!',
        'application_id': app_record.id,
        'status': app_record.status
    }), 200

# 10. POST /api/profile - Update profile details
@api.route('/profile', methods=['POST'])
def update_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401

    data = request.get_json() if request.is_json else request.form

    user.bio = data.get('bio', user.bio)
    user.skills = data.get('skills', user.skills)
    user.experience = data.get('experience', user.experience)
    user.education = data.get('education', user.education)

    db.session.commit()

    return jsonify({
        'message': 'Profile details updated successfully!',
        'profile': {
            'bio': user.bio,
            'skills': user.skills,
            'experience': user.experience,
            'education': user.education,
            'profile_picture': user.profile_picture,
            'resume_filename': user.resume_filename
        }
    }), 200

# 11. POST /api/profile/upload-picture - Upload/Update Profile avatar (Cloud or Local)
@api.route('/profile/upload-picture', methods=['POST'])
def upload_profile_picture():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401

    if 'profile_pic' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400

    file = request.files['profile_pic']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        try:
            filename_or_url, _ = upload_file_to_cloud_or_local(file, "avatars", is_image=True)
        except Exception as e:
            return jsonify({'error': f'Avatar upload failed: {str(e)}'}), 500
            
        user.profile_picture = filename_or_url
        db.session.commit()
        
        return jsonify({
            'message': 'Profile picture updated successfully!',
            'filename': filename_or_url
        }), 200
    else:
        return jsonify({'error': 'Invalid image type. Only PNG, JPG, JPEG, and GIF are allowed.'}), 400

# 12. POST /api/profile/upload-resume - Upload profile default resume
@api.route('/profile/upload-resume', methods=['POST'])
def upload_profile_resume():
    user = get_current_user()
    if not user or user.role != 'seeker':
        return jsonify({'error': 'Unauthorized. Seekers only.'}), 401

    if 'resume_file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400

    file = request.files['resume_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if file and allowed_file(file.filename, ALLOWED_RESUME_EXTENSIONS):
        try:
            filename_or_url, original_name = upload_file_to_cloud_or_local(file, "resumes", is_image=False)
        except Exception as e:
            return jsonify({'error': f'Resume upload failed: {str(e)}'}), 500
        
        user.resume_filename = original_name
        user.resume_filepath = filename_or_url
        db.session.commit()
        
        return jsonify({
            'message': 'Default resume uploaded successfully!',
            'filename': original_name
        }), 200
    else:
        return jsonify({'error': 'Invalid file type. Only PDF, DOC, and DOCX are allowed.'}), 400

# 13. POST /api/profile/change-password - Change profile account password
@api.route('/profile/change-password', methods=['POST'])
def change_password():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized. Please login.'}), 401

    data = request.get_json() if request.is_json else request.form
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        return jsonify({'error': 'All password fields are required.'}), 400

    if not check_password_hash(user.password, current_password):
        return jsonify({'error': 'Current password is incorrect.'}), 400

    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match.'}), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully!'}), 200

# 14. GET /api/uploads/<filename> - Public profile avatar local downloader
@api.route('/uploads/<path:filename>', methods=['GET'])
def get_uploaded_file(filename):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found.'}), 404
        
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], safe_filename)
