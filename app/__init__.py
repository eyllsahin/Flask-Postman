from flask import Flask
from dotenv import load_dotenv
import os

def create_app():
    # Load .env variables like SECRET_KEY
    load_dotenv()

    # Create Flask app instance
    app = Flask(__name__)

    # Set config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret')

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)

    return app
