from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class auth_users(db.Model):
    __tablename__ = 'auth_users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'seeker' or 'recruiter'
    
    # Profile Info
    bio = db.Column(db.Text, nullable=True)
    skills = db.Column(db.String(250), nullable=True)
    experience = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)
    
    # Uploaded Profile Picture and Resume Info
    profile_picture = db.Column(db.String(250), nullable=True)
    resume_filename = db.Column(db.String(250), nullable=True)
    resume_filepath = db.Column(db.String(250), nullable=True)

class Job(db.Model):
    __tablename__ = 'job'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.String(50), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.String(50), nullable=True)
    
    recruiter_id = db.Column(db.Integer, db.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=True)
    recruiter = db.relationship('auth_users', backref=db.backref('jobs', lazy=True, cascade='all, delete-orphan'))

class Application(db.Model):
    __tablename__ = 'application'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending') # Pending, Reviewed, Interviewing, Offered, Rejected
    cover_letter = db.Column(db.Text, nullable=True)
    resume_link = db.Column(db.String(250), nullable=True)
    date_applied = db.Column(db.String(50), nullable=True)
    
    # Uploaded Resume Info specific to the application
    resume_filename = db.Column(db.String(250), nullable=True)
    resume_filepath = db.Column(db.String(250), nullable=True)

    job = db.relationship('Job', backref=db.backref('applications', lazy=True, cascade='all, delete-orphan'))
    seeker = db.relationship('auth_users', backref=db.backref('applications', lazy=True))

# Performance Optimization Indexes
db.Index('idx_user_email', auth_users.email)
db.Index('idx_job_recruiter', Job.recruiter_id)
db.Index('idx_application_job', Application.job_id)
db.Index('idx_application_seeker', Application.seeker_id)