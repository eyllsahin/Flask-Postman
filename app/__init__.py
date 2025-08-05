from flask import Flask, render_template, redirect, url_for
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret')

    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Add console handler for all environments - this is our primary logging method
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    # In debug mode, skip file logging to avoid file access conflicts during development reloads
    if not app.debug:
        try:
            # Use a different log file for each process to avoid conflicts
            import uuid
            process_id = str(uuid.uuid4())[:8]
            log_file = f'logs/chatbot_{process_id}.log'
            
            file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=5, delay=True)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        except Exception as e:
            # Fall back to console logging if file logging fails
            print(f"Warning: Could not set up file logging: {e}")
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Chatbot startup')

    from .routes import main
    app.register_blueprint(main)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 error: {error}")
        return render_template('error.html', error_message="The page you're looking for doesn't exist in our magical realm."), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        return render_template('error.html', error_message="Our magical forest is experiencing some turbulence. Please try again later."), 500

    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.error(f"401 error: {error}")
        return redirect(url_for('main.login_page'))
        
    return app
