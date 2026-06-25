import os
from flask import Flask, render_template
from dotenv import load_dotenv
from routes.database import db
from routes.auth_routes import auth
from routes.api_routes import api
from extensions import mail
from sqlalchemy.pool import NullPool

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Base configurations & Postgres SQL dialect conversion
db_url = os.getenv("DATABASE_URL", "sqlite:///database.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "jobportal_secret_key_12345")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Serverless Database connection pooling adaptations
IS_VERCEL = os.getenv('VERCEL', 'False').lower() in ('true', '1')

engine_options = {
    "pool_pre_ping": True,
}

if IS_VERCEL:
    # Serverless Functions spin up dynamically: close connections on release to avoid Neon db connection exhaustion
    engine_options["poolclass"] = NullPool
else:
    engine_options["pool_recycle"] = 300
    engine_options["pool_size"] = 5
    engine_options["max_overflow"] = 10

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

# Session Security Policies
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")

# Mail Server Configurations from Environment
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1')
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME', ''))

# Writable Uploads Folder configuration adaptions (Read-only root folders on Vercel)
if IS_VERCEL:
    # Local files on Vercel are write-restricted except for /tmp
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Extensions
db.init_app(app)
mail.init_app(app)

# Create Database tables within Context
with app.app_context():
    db.create_all()

# Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(api, url_prefix='/api')

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True, port=9900)