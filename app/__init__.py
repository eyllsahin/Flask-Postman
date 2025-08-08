from flask import Flask, render_template, redirect, url_for
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

def create_app():
 
    load_dotenv(override=False)

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret')


    if not os.path.exists('logs'):
        os.mkdir('logs')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)

    if not app.debug:
        try:
            import uuid
            process_id = str(uuid.uuid4())[:8]
            log_file = f'logs/chatbot_{process_id}.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=5, delay=True)
            file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}")

    app.logger.setLevel(logging.INFO)
    app.logger.info('Chatbot startup')
    from .routes import main
    app.register_blueprint(main)

    @app.errorhandler(404)
    def not_found_error(error):
    
        from flask import request
        app.logger.error(f"404 error for URL '{request.url}' (path: '{request.path}', method: '{request.method}', user-agent: '{request.headers.get('User-Agent', 'Unknown')}'): {error}")
        return render_template('error.html', error_message="The page you're looking for doesn't exist in our magical realm."), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        return render_template('error.html', error_message="Our magical forest is experiencing some turbulence. Please try again later."), 500

    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.error(f"401 error: {error}")
        return redirect(url_for('main.login_page'))

    @app.after_request
    def add_no_cache_headers(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app
