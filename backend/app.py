from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from routes import api_bp
from routes.chat import chat_bp
from routes.export import export_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Register blueprints
app.register_blueprint(api_bp)
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(export_bp, url_prefix='/api/export')

@app.route('/')
def hello_world():
    return 'AI Chatbot API is running!'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)