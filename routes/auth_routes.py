import random
from functools import wraps
from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from routes.database import db, auth_users, Job
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mail
from flask_mail import Message

auth = Blueprint('auth', __name__)

# Authentication Decorator
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.')
                return redirect(url_for('auth.login'))
            if role and session.get('role') != role:
                flash('Access denied. You do not have permission to view this page.')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth.route('/login', methods=["GET", "POST"])
def login():
    if "full_name" in session:
        return redirect(url_for('auth.dashboard'))
    if request.method == "POST":
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = auth_users.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['full_name'] = user.full_name
            return redirect(url_for('auth.dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if "full_name" in session:
        return redirect(url_for('auth.dashboard'))
    if request.method == "POST":
        role = request.form.get('role')
        fullName = request.form.get('fullName', '').strip()
        password = request.form.get('password', '')
        confirmPassword = request.form.get('confirmPassword', '')
        email = request.form.get('email', '').strip()
        
        if not role or not fullName or not password or not email:
            return render_template('signup.html', error='All fields are required')
            
        existing_user = auth_users.query.filter_by(email=email).first()
        if existing_user:
            return render_template('signup.html', error='Email already registered')
            
        if password == confirmPassword:
            otp = str(random.randint(100000, 999999))
            
            session['pending_signup'] = {
                'fullName': fullName,
                'email': email,
                'password': password,
                'role': role
            }
            session['signup_otp'] = otp
            
            msg = Message(
                'OTP Verification - JobPortal',
                recipients=[email],
                body=f"Your OTP code is {otp}",
                html=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
                    <div style="background-color: #2563eb; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">Welcome to JobPortal</h1>
                    </div>
                    <div style="padding: 30px; color: #333; line-height: 1.6;">
                        <p style="font-size: 16px;">Hello,</p>
                        <p style="font-size: 16px;">Thank you for signing up. To complete your registration, please verify your email using the OTP below:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <span style="display: inline-block; font-size: 32px; font-weight: bold; letter-spacing: 5px; padding: 15px 30px; background-color: #f8f9fa; border: 2px dashed #2563eb; color: #2563eb; border-radius: 8px;">
                                {otp}
                            </span>
                        </div>
                        <p style="font-size: 14px; color: #666;">This code is valid for 10 minutes. Please do not share it with anyone.</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999; text-align: center;">&copy; 2026 JobPortal. All rights reserved.</p>
                    </div>
                </div>
                '''
            )
            
            # Send OTP email with graceful fallback if server fails
            send_success = False
            try:
                mail.send(msg)
                send_success = True
            except Exception as e:
                # Log SMTP error and print to console for development verification
                print(f"[DEVELOPMENT FALLBACK] SMTP Error sending signup OTP email: {e}")
                print(f"[OTP CODE FOR {email} IS: {otp}]")
            
            success_msg = "OTP code sent to your email!" if send_success else "Registration pending. (SMTP Offline: Please check console for verification code)"
            return render_template('otp_verification.html', email=email, success_msg=success_msg)
        else:
            return render_template('signup.html', error='Passwords do not match')
    return render_template('signup.html')

@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if "full_name" in session:
        return redirect(url_for('auth.dashboard'))
    if request.method == "POST":
        user_otp = request.form.get('otp', '').strip()
        if user_otp == session.get('signup_otp'):
            pending_data = session.get('pending_signup')
            if not pending_data:
                return render_template('signup.html', error='Session expired. Please signup again.')

            # Check once more if email exists before creating
            existing_user = auth_users.query.filter_by(email=pending_data['email']).first()
            if existing_user:
                return render_template('signup.html', error='Email already registered')

            new_user = auth_users(
                full_name=pending_data['fullName'],
                email=pending_data['email'],
                password=generate_password_hash(pending_data['password']),
                role=pending_data['role']
            )
            db.session.add(new_user)
            db.session.commit()

            # Automatically log the user in
            session['user_id'] = new_user.id
            session['role'] = new_user.role
            session['full_name'] = new_user.full_name

            # Clear signup session variables
            session.pop('pending_signup', None)
            session.pop('signup_otp', None)

            return redirect(url_for('auth.dashboard'))
        else:
            email = session.get('pending_signup', {}).get('email', '')
            return render_template('otp_verification.html', email=email, error='Incorrect OTP code')
    return redirect(url_for('auth.signup'))

@auth.route('/dashboard')
@login_required()
def dashboard():
    user = auth_users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    jobs = Job.query.order_by(Job.id.desc()).all()
    return render_template('dashboard.html', user=user, jobs=jobs)

@auth.route('/post-job', methods=['GET', 'POST'])
@login_required(role='recruiter')
def post_job():
    user = auth_users.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        company = request.form.get('company', '').strip()
        location = request.form.get('location', '').strip()
        salary = request.form.get('salary', '').strip()
        job_type = request.form.get('job_type', '').strip()
        experience = request.form.get('experience', '').strip()
        skills = request.form.get('skills', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title or not company or not location or not salary or not job_type or not experience or not skills or not description:
            flash('All job fields are required.')
            return render_template('post_job.html', user=user)
            
        date_str = datetime.now().strftime("%d %b %Y")
        
        new_job = Job(
            title=title,
            company=company,
            location=location,
            salary=salary,
            job_type=job_type,
            experience=experience,
            description=description,
            skills=skills,
            date_posted=date_str,
            recruiter_id=user.id
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('auth.dashboard'))
        
    return render_template('post_job.html', user=user)

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == "POST":
        email = request.form.get('email', '').strip()
        user = auth_users.query.filter_by(email=email).first()

        if user:
            otp = str(random.randint(100000, 999999))
            session['reset_otp'] = otp
            session['reset_email'] = email

            msg = Message(
                'Password Reset OTP - JobPortal',
                recipients=[email],
                body=f"Your password reset OTP is {otp}",
                html=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden;">
                    <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">Password Reset</h1>
                    </div>
                    <div style="padding: 30px; color: #333; line-height: 1.6;">
                        <p style="font-size: 16px;">Hello,</p>
                        <p style="font-size: 16px;">We received a request to reset your password. Use the verification OTP code below to proceed:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <span style="display: inline-block; font-size: 32px; font-weight: bold; letter-spacing: 5px; padding: 15px 30px; background-color: #f8f9fa; border: 2px dashed #dc3545; color: #dc3545; border-radius: 8px;">
                                {otp}
                            </span>
                        </div>
                        <p style="font-size: 14px; color: #666;">If you did not request this, please ignore this email. Your password will remain unchanged.</p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                        <p style="font-size: 12px; color: #999; text-align: center;">&copy; 2026 JobPortal. All rights reserved.</p>
                    </div>
                </div>
                '''
            )
            
            send_success = False
            try:
                mail.send(msg)
                send_success = True
            except Exception as e:
                print(f"[DEVELOPMENT FALLBACK] SMTP Error sending password recovery email: {e}")
                print(f"[OTP CODE FOR {email} IS: {otp}]")
                
            success_msg = "Reset OTP sent to your email!" if send_success else "Recovery pending. (SMTP Offline: Code printed to system log/console)"
            return render_template('reset_otp.html', email=email, success_msg=success_msg)
        else:
            return render_template('forgot_password.html', error='Email is not registered!')

    return render_template('forgot_password.html')

@auth.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    otp = request.form.get('otp', '').strip()
    if otp == session.get('reset_otp'):
        session['reset_verified'] = True
        return redirect(url_for('auth.reset_password'))
    else:
        email = session.get('reset_email', '')
        return render_template('reset_otp.html', email=email, error='Invalid OTP code!')

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_verified'):
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == "POST":
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password:
            return render_template('reset_password.html', error='Password cannot be blank')

        if new_password == confirm_password:
            email = session.get('reset_email')
            user = auth_users.query.filter_by(email=email).first()
            if user:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                
                # Cleanup reset session variables
                session.pop('reset_otp', None)
                session.pop('reset_email', None)
                session.pop('reset_verified', None)
                
                flash('Password updated successfully!')
                return redirect(url_for('auth.login'))
            return render_template('reset_password.html', error='User not found!')
        else:
            return render_template('reset_password.html', error='Passwords do not match!')

    return render_template('reset_password.html')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))